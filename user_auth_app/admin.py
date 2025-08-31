from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db import transaction, connection
from django.utils import timezone
from django.apps import apps
from quiz_management_app.models import Quiz, Question, QuestionOption


class CustomUserAdmin(UserAdmin):
    def delete_queryset(self, request, queryset):
        """
        Überschreibt die delete_queryset Methode, um sicherzustellen,
        dass alle zugehörigen Daten gelöscht werden
        """
        with transaction.atomic():
            for user in queryset:
                # Aggressive Lösung: Lösche alle Foreign Key Beziehungen direkt in der DB
                self._delete_all_user_relations_direct(user)
                
                # Lösche User Groups und Permissions
                user.groups.clear()
                user.user_permissions.clear()
            
            # Jetzt können wir den Benutzer sicher löschen
            super().delete_queryset(request, queryset)
    
    def _delete_all_user_relations_direct(self, user):
        """
        Löscht alle Foreign Key Beziehungen direkt in der Datenbank
        """
        with connection.cursor() as cursor:
            # Hole alle Tabellen, die Foreign Keys zu auth_user haben
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name != 'auth_user'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                try:
                    # Prüfe ob die Tabelle eine user_id oder created_by Spalte hat
                    cursor.execute("PRAGMA table_info({})".format(table))
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    # Mögliche Foreign Key Spalten zu User
                    user_columns = ['user_id', 'created_by_id', 'owner_id', 'author_id', 'creator_id']
                    
                    for col in user_columns:
                        if col in columns:
                            # Lösche alle Einträge, die auf diesen User verweisen
                            cursor.execute("DELETE FROM {} WHERE {} = %s".format(table, col), [user.id])
                            print("Gelöscht aus {}.{}: {} Einträge".format(table, col, cursor.rowcount))
                
                except Exception as e:
                    print("Fehler beim Löschen aus {}: {}".format(table, e))
                    continue
    
    def _delete_jwt_tokens(self, user):
        """
        Löscht JWT-Token-Daten für einen Benutzer
        """
        try:
            # Prüfe ob die Token-Blacklist-App installiert ist
            from django.apps import apps
            if apps.is_installed('rest_framework_simplejwt.token_blacklist'):
                from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
                OutstandingToken.objects.filter(user=user).delete()
        except (ImportError, AttributeError, Exception) as e:
            # Ignoriere Fehler bei JWT-Token-Löschung
            print(f"JWT-Token-Löschung übersprungen: {e}")
            pass
    
    def _delete_all_user_relations(self, user):
        """
        Löscht automatisch alle Foreign Key Beziehungen zu einem Benutzer
        """
        # Hole alle Modelle aus allen Apps
        all_models = apps.get_models()
        
        for model in all_models:
            # Prüfe alle Felder des Modells
            for field in model._meta.fields:
                if hasattr(field, 'related_model') and field.related_model == User:
                    # Dies ist ein Foreign Key zu User
                    try:
                        # Lösche alle Objekte, die auf diesen User verweisen
                        filter_kwargs = {field.name: user}
                        model.objects.filter(**filter_kwargs).delete()
                    except Exception as e:
                        # Logge Fehler, aber fahre fort
                        print(f"Fehler beim Löschen von {model.__name__}.{field.name}: {e}")
                        continue


# Registriere die benutzerdefinierte UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
