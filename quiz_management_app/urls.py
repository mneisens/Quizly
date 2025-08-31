from django.urls import path, include

urlpatterns = [
    path('api/', include('quiz_management_app.api.urls')),
]
