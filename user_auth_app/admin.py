from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db import connection
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )
    
    def delete_model(self, request, obj):
        try:
            self._delete_jwt_tokens(obj)
            self._delete_from_table('auth_user', 'id', obj.id)
        except Exception as e:
            raise ValidationError(f"Fehler beim Löschen des Benutzers: {e}")
    
    def _delete_from_table(self, table, col, user_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM {table} WHERE {col} = %s", [user_id])
        except Exception as e:
            raise
    
    def _delete_jwt_tokens(self, user):
        try:
            OutstandingToken.objects.filter(user_id=user.id).delete()
            BlacklistedToken.objects.filter(token__user_id=user.id).delete()
        except Exception:
            pass
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            try:
                self.delete_model(request, obj)
            except Exception:
                pass
