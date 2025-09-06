from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of an object to edit it"""
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission for object"""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """Custom permission to allow read access to anyone, but write access only to authenticated users"""
    
    def has_permission(self, request, view):
        """Check if user has permission for view"""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated