"""
apps/accounts/api_views.py
--------------------------
REST API endpoints consumed by the Flutter mobile app.

Endpoints
---------
POST /api/auth/login/     → returns {access, refresh, user} on success
POST /api/auth/register/  → creates a new user; returns 201 on success
GET  /api/auth/me/        → returns the current authenticated user profile
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def _user_payload(user: User) -> dict:
    """Return a safe dict of user fields for API responses."""
    return {
        'id':            user.pk,
        'username':      user.username,
        'email':         user.email,
        'first_name':    user.first_name,
        'last_name':     user.last_name,
        'role':          user.role,
        'organisation':  user.organisation_id,
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    Authenticate a user and return JWT tokens.

    Request body: { "username": "...", "password": "..." }
    Response 200: { "access": "...", "refresh": "...", "user": {...} }
    Response 401: { "detail": "Invalid credentials" }
    """
    from django.contrib.auth import authenticate

    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response({'detail': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({'detail': 'Account is disabled.'}, status=status.HTTP_403_FORBIDDEN)

    refresh = RefreshToken.for_user(user)
    return Response({
        'access':  str(refresh.access_token),
        'refresh': str(refresh),
        'user':    _user_payload(user),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """
    Register a new user account.

    Request body:
        { "username", "password", "email", "first_name", "last_name",
          "role" (optional), "organisation" (optional, int pk) }
    Response 201: {}
    Response 400: { field: [errors] }
    """
    data = request.data

    required = ['username', 'password', 'email']
    errors = {f: ['This field is required.'] for f in required if not data.get(f)}
    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=data['username']).exists():
        return Response({'username': ['A user with that username already exists.']},
                        status=status.HTTP_400_BAD_REQUEST)

    allowed_roles = [r[0] for r in User.RoleChoices.choices]
    role = data.get('role', User.RoleChoices.EMPLOYEE)
    if role not in allowed_roles:
        return Response({'role': [f'Invalid role. Allowed: {allowed_roles}']},
                        status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=data['username'],
        password=data['password'],
        email=data.get('email', ''),
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        role=role,
        organisation_id=data.get('organisation') or None,
    )
    return Response({'detail': 'Account created successfully.'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_me(request):
    """Return the authenticated user's profile."""
    return Response(_user_payload(request.user))
