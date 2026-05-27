from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Organisation, OrganisationApplication, ApplicationResource


# ── Organisation ──────────────────────────────────────────────────────────────

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display       = ('logo_preview', 'name', 'approval_badge', 'approved_at', 'created_at')
    list_display_links = ('name',)
    search_fields      = ('name',)
    list_filter        = ('is_approved', 'created_at')
    ordering           = ('-created_at',)
    readonly_fields    = ('logo_preview', 'approved_at', 'created_at', 'updated_at')
    actions            = ('approve_organisations', 'revoke_organisations')

    fieldsets = (
        (None, {
            'fields': ('name', 'logo', 'logo_preview'),
        }),
        ('Approval', {
            'fields': ('is_approved', 'approved_at'),
            'description': (
                'Approving an organisation makes it and all its resources '
                'visible to users. Revoking hides them immediately.'
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="height:48px;width:48px;object-fit:cover;'
                'border-radius:8px;border:1px solid #334155;" />',
                obj.logo.url
            )
        return format_html(
            '<div style="height:48px;width:48px;border-radius:8px;background:#1e2937;'
            'border:1px solid #334155;display:flex;align-items:center;justify-content:center;'
            'font-size:20px;">🏢</div>'
        )
    logo_preview.short_description = 'Logo'

    @admin.display(description='Status', boolean=False)
    def approval_badge(self, obj):
        if obj.is_approved:
            return format_html(
                '<span style="background:#22c55e;color:#fff;padding:2px 10px;'
                'border-radius:12px;font-size:0.75rem;font-weight:700;">Approved</span>'
            )
        return format_html(
            '<span style="background:#ef4444;color:#fff;padding:2px 10px;'
            'border-radius:12px;font-size:0.75rem;font-weight:700;">Pending</span>'
        )

    # ------------------------------------------------------------------
    # Bulk actions
    # ------------------------------------------------------------------
    @admin.action(description='Approve selected organisations (activates their resources)')
    def approve_organisations(self, request, queryset):
        from apps.resources.models import Resource
        now = timezone.now()
        count = 0
        for org in queryset.filter(is_approved=False):
            org.is_approved = True
            org.approved_at = now
            org.save(update_fields=['is_approved', 'approved_at', 'updated_at'])
            Resource.objects.filter(organisation=org).update(is_active=True)
            count += 1
        self.message_user(request, f'{count} organisation(s) approved and resources activated.')

    @admin.action(description='Revoke approval for selected organisations (hides their resources)')
    def revoke_organisations(self, request, queryset):
        from apps.resources.models import Resource
        count = 0
        for org in queryset.filter(is_approved=True):
            org.is_approved = False
            org.approved_at = None
            org.save(update_fields=['is_approved', 'approved_at', 'updated_at'])
            Resource.objects.filter(organisation=org).update(is_active=False)
            count += 1
        self.message_user(request, f'{count} organisation(s) revoked and resources hidden.')


# ── OrganisationApplication ───────────────────────────────────────────────────

class ApplicationResourceInline(admin.TabularInline):
    model = ApplicationResource
    extra = 0
    readonly_fields = ('verified_at', 'created_at', 'updated_at')
    show_change_link = True


@admin.register(OrganisationApplication)
class OrganisationApplicationAdmin(admin.ModelAdmin):
    list_display  = (
        'organisation_name', 'contact_email', 'status',
        'created_organisation_link', 'submitted_at', 'reviewed_at',
    )
    list_filter   = ('status', 'submitted_at', 'reviewed_at')
    search_fields = ('organisation_name', 'contact_name', 'contact_email')
    readonly_fields = (
        'verification_token', 'submitted_at', 'updated_at',
        'created_organisation_link',
    )
    inlines = (ApplicationResourceInline,)
    actions = ('activate_applications',)

    @admin.display(description='Linked Organisation')
    def created_organisation_link(self, obj):
        if obj.created_organisation:
            url = (
                f'/admin/core/organisation/{obj.created_organisation.pk}/change/'
            )
            badge = (
                '<span style="background:#22c55e;color:#fff;padding:1px 8px;'
                'border-radius:10px;font-size:0.7rem;margin-left:6px;">✓ Approved</span>'
                if obj.created_organisation.is_approved else ''
            )
            return format_html(
                '<a href="{}">{}</a>{}', url, obj.created_organisation.name, badge
            )
        return format_html('<span style="color:#94a3b8;">—</span>')

    @admin.action(description='Activate selected applications (create org + resources)')
    def activate_applications(self, request, queryset):
        """
        For each selected application that is not yet Completed:
        1. Create (or reuse) the linked Organisation and mark it approved.
        2. Create Resource records for every verified ApplicationResource.
        3. Mark the application as Completed.
        """
        from apps.resources.models import Resource
        now = timezone.now()
        activated = 0

        for app in queryset.exclude(status=OrganisationApplication.StatusChoices.COMPLETED):
            # 1. Create or reuse the Organisation
            if app.created_organisation:
                org = app.created_organisation
            else:
                org = Organisation.objects.create(
                    name=app.organisation_name,
                    logo=app.logo or None,
                )
                app.created_organisation = org

            # Approve the organisation
            if not org.is_approved:
                org.is_approved = True
                org.approved_at = now
                org.save(update_fields=['is_approved', 'approved_at', 'updated_at'])

            # 2. Create Resource records for verified ApplicationResources
            #    Skip any that already have a matching resource in this org
            existing_names = set(
                Resource.objects.filter(organisation=org)
                .values_list('name', flat=True)
            )
            for app_res in app.resources.filter(
                status=ApplicationResource.StatusChoices.VERIFIED
            ):
                if app_res.name not in existing_names:
                    Resource.objects.create(
                        organisation=org,
                        name=app_res.name,
                        category=app_res.category,
                        description=app_res.description,
                        price=app_res.price,
                        is_active=True,
                    )

            # 3. Mark application as Completed
            app.status = OrganisationApplication.StatusChoices.COMPLETED
            app.reviewed_at = app.reviewed_at or now
            app.save(update_fields=[
                'status', 'reviewed_at', 'created_organisation', 'updated_at'
            ])
            activated += 1

        self.message_user(
            request,
            f'{activated} application(s) activated. Organisations approved and resources created.',
        )


@admin.register(ApplicationResource)
class ApplicationResourceAdmin(admin.ModelAdmin):
    list_display  = ('name', 'application', 'category', 'price', 'status', 'verified_at')
    list_filter   = ('status', 'category', 'created_at')
    search_fields = ('name', 'application__organisation_name')
    readonly_fields = ('verified_at', 'created_at', 'updated_at')
