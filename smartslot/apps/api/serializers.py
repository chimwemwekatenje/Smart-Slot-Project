import uuid
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.core.models import Organisation
from apps.resources.models import Resource
from apps.bookings.models import Booking

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    # Employees provide their org's invite code or org id; externals leave blank
    organisation_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'password', 'role', 'phone', 'organisation_id')
        read_only_fields = ('id',)
        extra_kwargs = {'role': {'required': False}, 'phone': {'required': False}}

    def create(self, validated_data):
        org_id = validated_data.pop('organisation_id', None)
        password = validated_data.pop('password')
        # Default role: External unless they link to an org (then Employee)
        if 'role' not in validated_data or not validated_data['role']:
            validated_data['role'] = 'Employee' if org_id else 'External'
        if org_id:
            try:
                validated_data['organisation'] = Organisation.objects.get(pk=org_id)
            except Organisation.DoesNotExist:
                raise serializers.ValidationError({'organisation_id': 'Organisation not found.'})
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    organisation_name = serializers.CharField(
        source='organisation.name', read_only=True, default=None)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'role', 'phone', 'organisation', 'organisation_name')


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ('id', 'name', 'created_at', 'updated_at')


class ResourceSerializer(serializers.ModelSerializer):
    organisation_name = serializers.CharField(source='organisation.name', read_only=True)
    photo_url = serializers.SerializerMethodField()

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get('request')
        # obj.photo.url returns e.g. /media/resources_photos/img.jpg
        url = obj.photo.url
        # Ensure it starts with / so build_absolute_uri works correctly
        if not url.startswith('/'):
            url = '/' + url
        if request:
            return request.build_absolute_uri(url)
        # Fallback: use SITE_URL from settings
        from django.conf import settings
        site = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
        return f"{site}{url}"

    class Meta:
        model = Resource
        fields = ('id', 'name', 'description', 'photo', 'photo_url', 'price',
                  'category', 'custom_fields', 'organisation',
                  'organisation_name', 'created_at', 'updated_at')


class BookingSerializer(serializers.ModelSerializer):
    resource_name = serializers.CharField(source='resource.name', read_only=True)
    resource_category = serializers.CharField(source='resource.category', read_only=True)
    resource_price = serializers.DecimalField(
        source='resource.price', max_digits=10, decimal_places=2, read_only=True)
    resource_type = serializers.CharField(source='resource.category', read_only=True)
    organisation_name = serializers.CharField(source='organisation.name', read_only=True)
    booked_by = serializers.SerializerMethodField()
    payment_url = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    def get_photo_url(self, obj):
        if not obj.resource.photo:
            return None
        request = self.context.get('request')
        url = obj.resource.photo.url
        if not url.startswith('/'):
            url = '/' + url
        if request:
            return request.build_absolute_uri(url)
        from django.conf import settings
        site = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
        return f"{site}{url}"

    def get_booked_by(self, obj):
        u = obj.user
        full = f"{u.first_name} {u.last_name}".strip()
        return full if full else u.username

    def get_payment_url(self, obj):
        """Generate PayChangu payment URL if this is a paid booking."""
        if obj.resource.price <= 0:
            return None
        try:
            from apps.payments.services import initiate_payment
            checkout_url, _ = initiate_payment(
                booking=obj,
                customer_email=obj.user.email or '',
                customer_first_name=obj.user.first_name or obj.user.username,
                customer_last_name=obj.user.last_name or '',
            )
            return checkout_url
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f'Failed to generate PayChangu URL for booking {obj.id}: {e}')
            return None

    class Meta:
        model = Booking
        fields = ('id', 'resource', 'resource_name', 'resource_category',
                  'resource_type', 'resource_price', 'photo_url',
                  'organisation_name', 'booked_by',
                  'start_time', 'end_time', 'status',
                  'qr_token', 'custom_data', 'payment_url', 'issued_at', 'verified_at',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'status', 'qr_token', 'payment_url', 'issued_at',
                            'verified_at', 'created_at', 'updated_at')


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ('resource', 'start_time', 'end_time', 'custom_data')

    def validate(self, data):
        start, end = data['start_time'], data['end_time']
        if end <= start:
            raise serializers.ValidationError("End time must be after start time.")
        conflict = Booking.objects.filter(
            resource=data['resource'],
            status__in=['Pending', 'Issued', 'Verified'],
            start_time__lt=end,
            end_time__gt=start,
        ).exists()
        if conflict:
            raise serializers.ValidationError(
                "This resource is already booked for the selected time.")
        return data

    def create(self, validated_data):
        validated_data['qr_token'] = str(uuid.uuid4())
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['organisation'] = validated_data['resource'].organisation
        # All bookings are issued immediately upon creation
        validated_data['status'] = 'Issued'
        instance = super().create(validated_data)
        return instance

    def to_representation(self, instance):
        return BookingSerializer(instance, context=self.context).data
