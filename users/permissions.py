from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_authenticated and request.user.is_admin_user


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin_user


class IsDonorUser(permissions.BasePermission):
    """
    Custom permission to only allow donor users.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_donor


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners or admins to access objects.
    """

    def has_object_permission(self, request, view, obj):
        # Allow if user is admin
        if request.user.is_admin_user:
            return True

        # Allow if user owns the object
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "created_by"):
            return obj.created_by == request.user
        if hasattr(obj, "donor"):
            return obj.donor == request.user

        return obj == request.user


class IsVerifiedUser(permissions.BasePermission):
    """
    Custom permission to only allow verified users.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_verified


class IsActiveCase(permissions.BasePermission):
    """
    Custom permission to check if charity case is active for donations.
    """

    def has_permission(self, request, view):
        # This will be used at the object level
        return True

    def has_object_permission(self, request, view, obj):
        # Check if case is active (approved and not completed)
        if hasattr(obj, "is_active"):
            return obj.is_active
        return True
