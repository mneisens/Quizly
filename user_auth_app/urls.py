from django.urls import path, include

urlpatterns = [
    path('api/', include('user_auth_app.api.urls')),
]
