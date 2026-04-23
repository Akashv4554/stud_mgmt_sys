"""
accounts/views.py
"""

from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .serializers import UserSerializer, UserCreateSerializer, ChangePasswordSerializer

User = get_user_model()


class IsAdminUser(permissions.BasePermission):
    """Only admin-role users may access."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD for User accounts (admin-only for list/create/delete).
    Any authenticated user can view/update their own profile via /me/.
    """
    queryset = User.objects.all().order_by("id")
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["role", "is_active"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["username", "date_joined"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ("list", "create", "destroy"):
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):
        """Return or update the currently authenticated user."""
        if request.method == "GET":
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        serializer = UserSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )
