from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .serializers import UserRegistrationSerializer, UserSerializer
from .auth_utils import (
    validate_login_credentials, authenticate_user, create_refresh_token_for_user,
    create_login_response_data, set_auth_cookies, blacklist_access_token,
    blacklist_refresh_token, blacklist_header_token, get_access_token_from_request,
    validate_access_token, get_refresh_token_from_request, refresh_access_token,
    create_refresh_response_data, set_refresh_cookie, normalize_registration_data,
    validate_password_match, remove_password2_from_data
)


class UserRegistrationView(CreateAPIView):
    """View for user registration"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Handles user registration"""
        normalized_data = normalize_registration_data(request.data)
        serializer = self.get_serializer(data=normalized_data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "detail": "User created successfully!"
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(GenericAPIView):
    """View for user login"""
    permission_classes = [AllowAny]
    
    
    def post(self, request, *args, **kwargs):
        """Handles user login"""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not validate_login_credentials(username, password):
            return Response({
                "detail": "Username und Passwort sind erforderlich."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate_user(username, password)
        
        if user is None:
            return Response({
                "detail": "Ungültige Anmeldedaten."
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh_token = create_refresh_token_for_user(user)
        response_data = create_login_response_data(user, refresh_token)
        response = Response(response_data, status=status.HTTP_200_OK)
        set_auth_cookies(response, refresh_token)
        
        return response


@method_decorator(csrf_exempt, name='dispatch')
class UserLogoutView(GenericAPIView):
    """View for user logout"""
    permission_classes = [IsAuthenticated]
    
    
    def post(self, request, *args, **kwargs):
        """Handles user logout"""
        try:
            access_token = request.COOKIES.get('access_token')
            refresh_token = request.COOKIES.get('refresh_token')
            
            blacklist_access_token(access_token)
            blacklist_refresh_token(refresh_token)
            blacklist_header_token(request)
            
            response = Response({
                "detail": "Log-Out successfully! All tokens have been invalidated."
            }, status=status.HTTP_200_OK)
            
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            
            return response
            
        except Exception as e:
            return Response({
                "detail": f"Fehler beim Logout: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class TokenValidationView(GenericAPIView):
    """View for token validation"""
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """Validates current authentication status"""
        access_token = get_access_token_from_request(request)
        user, token_or_error = validate_access_token(access_token)
        
        if user is None:
            return Response({
                "authenticated": False,
                "detail": token_or_error
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            "authenticated": True,
            "user": UserSerializer(user).data,
            "token_exp": token_or_error.payload.get('exp')
        }, status=status.HTTP_200_OK)


class TokenRefreshView(GenericAPIView):
    """View for token refresh"""
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Handles token refresh"""
        refresh_token = get_refresh_token_from_request(request)
        access_token, error = refresh_access_token(refresh_token)
        
        if access_token is None:
            return Response({
                "detail": error
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        response_data = create_refresh_response_data(access_token)
        response = Response(response_data, status=status.HTTP_200_OK)
        set_refresh_cookie(response, access_token)
        
        return response