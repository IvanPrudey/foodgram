from rest_framework.permissions import (
    BasePermission,
    IsAuthenticatedOrReadOnly,
    SAFE_METHODS
)


class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_staff)


class IsAdminAuthorOrReadOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        return (request.method in ('GET',)
                or obj.author == request.user
                or request.user.is_staff)


class IsAdminOrAuthorOrReadOnly(IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_superuser
            or obj.author == request.user
        )
