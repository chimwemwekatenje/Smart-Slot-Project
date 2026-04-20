"""
apps/resources/views.py
-----------------------
Multi-tenant resource views.

Access rules
------------
- PlatformAdmin  → sees resources from ALL organisations.
- Everyone else  → sees ONLY resources that belong to their own organisation.

All data access goes through  apps.resources.services  — never directly to
Firestore or Django ORM from inside views.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render
from django.core.exceptions import PermissionDenied

from apps.core.services import get_org_id_for_user
from apps.resources.services import (
    get_resources_for_organisation,
    get_all_resources,
    search_resources,
    get_categories_for_organisation,
)


class ResourceListView(LoginRequiredMixin, View):
    """
    List resources scoped to the current user's organisation.

    PlatformAdmin users see all resources across every organisation.
    """

    template_name = 'resources/resource_list.html'

    def get(self, request):
        user = request.user

        # ── Determine which org (or no restriction) ────────────────────────
        try:
            org_id = get_org_id_for_user(user)   # None for PlatformAdmin
        except PermissionDenied as exc:
            return render(request, 'errors/403.html', {'message': str(exc)}, status=403)

        # ── Optional filters from query string ─────────────────────────────
        query    = request.GET.get('q', '').strip()
        category = request.GET.get('category', '').strip()

        # ── Fetch resources ────────────────────────────────────────────────
        if user.is_platform_admin:
            # Super-admin: all orgs — filtering is post-fetch in Python
            resources = get_all_resources()
            if query:
                q = query.lower()
                resources = [r for r in resources if q in r.get('name', '').lower()]
            if category and category != 'All':
                resources = [r for r in resources if r.get('category') == category]
            # Collect categories from the full unfiltered set for the sidebar
            all_cats = sorted({r.get('category', '') for r in get_all_resources() if r.get('category')})
        else:
            resources = search_resources(org_id, query=query, category=category)
            all_cats = get_categories_for_organisation(org_id)

        # ── Build context ──────────────────────────────────────────────────
        is_external = not user.is_authenticated or (
            hasattr(user, 'role') and user.role == 'External'
        )

        context = {
            'resources':        resources,
            'is_external':      is_external,
            'is_authenticated': user.is_authenticated,
            'categories':       ['All'] + all_cats,
            'current_query':    query,
            'current_category': category,
        }
        return render(request, self.template_name, context)
