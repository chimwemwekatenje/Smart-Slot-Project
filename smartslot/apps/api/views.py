from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from apps.core.models import Organisation
from apps.resources.models import Resource
from apps.bookings.models import Booking
from .serializers import (
    RegisterSerializer, UserSerializer, OrganisationSerializer,
    ResourceSerializer, BookingSerializer, BookingCreateSerializer,
)

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Account created.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {'detail': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


class OrganisationListView(generics.ListAPIView):
    """Public list of organisations so external users can browse/filter by org."""
    serializer_class = OrganisationSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Organisation.objects.all().order_by('name')


class ResourceListView(generics.ListAPIView):
    """
    - External users: all resources from all orgs (read-only browse)
    - Employees: only resources from their own organisation
    """
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Resource.objects.select_related('organisation').all()

        # Employees only see their own org
        if user.role == 'Employee' and user.organisation:
            qs = qs.filter(organisation=user.organisation)

        q = self.request.query_params.get('q')
        cat = self.request.query_params.get('category')
        org = self.request.query_params.get('organisation')
        if q:
            qs = qs.filter(name__icontains=q)
        if cat:
            qs = qs.filter(category=cat)
        if org:
            qs = qs.filter(organisation_id=org)
        return qs


class MyBookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user
        ).select_related('resource').order_by('-created_at')


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # External users cannot book directly — they contact the org
        if request.user.role == 'External':
            return Response(
                {'detail': 'External users cannot book directly. Please contact the organisation.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)


class BookingUpdateView(generics.UpdateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('status')
        if new_status == 'Cancelled' and instance.status == 'Pending':
            instance.status = 'Cancelled'
            instance.save()
            return Response(BookingSerializer(instance).data)
        return Response({'detail': 'Not allowed.'}, status=status.HTTP_400_BAD_REQUEST)


class OrgResourceListView(generics.ListAPIView):
    """Resources for the logged-in employee's organisation (Org Panel tab)."""
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.organisation:
            return Resource.objects.filter(
                organisation=user.organisation).select_related('organisation')
        return Resource.objects.none()


class OrgBookingListView(generics.ListAPIView):
    """All bookings for the logged-in employee's organisation."""
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.organisation:
            return Booking.objects.filter(
                resource__organisation=user.organisation
            ).select_related('resource').order_by('-created_at')
        return Booking.objects.none()


class ResourceScheduleView(APIView):
    """Returns active bookings for a resource within a date range for the timetable."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        from datetime import datetime, timedelta
        # Default: current week (Mon–Sun)
        week_start_str = request.query_params.get('week_start')
        if week_start_str:
            try:
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d')
            except ValueError:
                week_start = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0)
        else:
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        week_end = week_start + timedelta(days=7)

        bookings = Booking.objects.filter(
            resource_id=pk,
            status__in=['Pending', 'Issued', 'Verified'],
            start_time__lt=week_end,
            end_time__gt=week_start,
        ).values('id', 'start_time', 'end_time', 'status')

        return Response(list(bookings))
