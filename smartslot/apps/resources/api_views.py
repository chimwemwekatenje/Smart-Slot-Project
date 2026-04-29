"""
apps/resources/api_views.py
---------------------------
REST API endpoints for resources — consumed by the Flutter mobile app.

Endpoints
---------
GET  /api/resources/                → list resources for the user's org
GET  /api/resources/<id>/           → detail for a single resource
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied

from apps.core.services import get_org_id_for_user
from apps.resources.services import (
    get_resources_for_organisation,
    get_all_resources,
    get_resource_by_id,
    search_resources,
    get_categories_for_organisation,
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_resource_list(request):
    """
    Return resources scoped to the current user's organisation.
    PlatformAdmin users see resources from all organisations.

    Query params: q (search), category
    """
    user = request.user
    try:
        org_id = get_org_id_for_user(user)
    except PermissionDenied as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

    query    = request.query_params.get('q', '').strip()
    category = request.query_params.get('category', '').strip()

    if user.is_platform_admin:
        resources = get_all_resources()
        if query:
            resources = [r for r in resources if query.lower() in r.get('name', '').lower()]
        if category and category != 'All':
            resources = [r for r in resources if r.get('category') == category]
    else:
        resources = search_resources(org_id, query=query, category=category)
        categories = get_categories_for_organisation(org_id)

    return Response(resources)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_resource_detail(request, pk: int):
    """Return a single resource by pk (scoped to user's org)."""
    user = request.user
    try:
        org_id = get_org_id_for_user(user)
    except PermissionDenied as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

    if user.is_platform_admin:
        resources = get_all_resources()
        matches = [r for r in resources if r['id'] == pk]
        resource = matches[0] if matches else None
    else:
        resource = get_resource_by_id(org_id, pk)

    if resource is None:
        return Response({'detail': 'Resource not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(resource)
