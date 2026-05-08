from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ('username', 'email', 'first_name', 'last_name',
                     'role', 'organisation', 'is_staff', 'is_active')
    list_filter   = ('role', 'organisation', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    date_hierarchy = 'date_joined'
    ordering      = ('-date_joined',)
    autocomplete_fields = ('organisation',)

    fieldsets = UserAdmin.fieldsets + (
        ('SmartSlot', {'fields': ('role', 'organisation')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('SmartSlot', {'fields': ('role', 'organisation')}),
    )

    # ------------------------------------------------------------------
    # Multi-tenancy: PlatformAdmin sees all users;
    # OrgAdmin sees only users in their own organisation.
    # ------------------------------------------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == 'PlatformAdmin':
            return qs
        if request.user.role == 'OrganisationAdmin' and request.user.organisation:
            return qs.filter(organisation=request.user.organisation)
        return qs.none()

    def save_model(self, request, obj, form, change):
        # When an OrgAdmin creates a user, force them into the same org.
        if (
            not request.user.is_superuser
            and request.user.role == 'OrganisationAdmin'
            and request.user.organisation
        ):
            obj.organisation = request.user.organisation
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # OrgAdmin cannot promote anyone to PlatformAdmin or superuser
        if not request.user.is_superuser:
            if 'is_superuser' in form.base_fields:
                form.base_fields['is_superuser'].disabled = True
            if 'role' in form.base_fields:
                from django.forms import ChoiceField
                allowed = [
                    c for c in User.RoleChoices.choices
                    if c[0] != 'PlatformAdmin'
                ]
                form.base_fields['role'].choices = allowed
        return form
