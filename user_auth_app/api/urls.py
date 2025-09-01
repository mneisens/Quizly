from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='refresh_token'),
    path('token/validate/', views.TokenValidationView.as_view(), name='validate_token'),
    path('debug/', views.DebugAuthView.as_view(), name='debug_auth'),
    path('test/', views.TestAuthView.as_view(), name='test_auth'),
    path('protected-test/', views.ProtectedTestView.as_view(), name='protected_test'),
]
