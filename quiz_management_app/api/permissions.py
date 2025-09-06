from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """Custom permission to only allow owners to edit their objects"""
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission for object"""
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return obj.created_by == request.user
