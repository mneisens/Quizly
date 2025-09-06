from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .serializers import UserRegistrationSerializer, UserSerializer


class UserRegistrationView(CreateAPIView):
    """View for user registration"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def _normalize_registration_data(self, data):
        """Normalizes registration data format"""
        normalized_data = data.copy()
        if 'confirmed_password' in normalized_data:
            normalized_data['password2'] = normalized_data.pop('confirmed_password')
        return normalized_data
    
    def _create_success_response(self):
        """Creates success response for registration"""
        return Response({
            "detail": "User created successfully!"
        }, status=status.HTTP_201_CREATED)
    
    def create(self, request, *args, **kwargs):
        """Handles user registration"""
        normalized_data = self._normalize_registration_data(request.data)
        serializer = self.get_serializer(data=normalized_data)
        
        if serializer.is_valid():
            serializer.save()
            return self._create_success_response()
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(GenericAPIView):
    """View for user login"""
    permission_classes = [AllowAny]
    
    def _validate_login_credentials(self, username, password):
        """Validates login credentials"""
        if not username or not password:
            return False
        return True
    
    def _authenticate_user(self, username, password):
        """Authenticates user with credentials"""
        return authenticate(username=username, password=password)
    
    def _create_login_response(self, user, refresh_token):
        """Creates login response with tokens"""
        response_data = {
            "detail": "Login successfully!",
            "user": UserSerializer(user).data,
            "access_token": str(refresh_token.access_token),
            "refresh_token": str(refresh_token)
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
    def _set_auth_cookies(self, response, refresh_token):
        """Sets authentication cookies"""
        response.set_cookie(
            'access_token', 
            str(refresh_token.access_token), 
            httponly=True, 
            samesite='Lax',
            max_age=3600,
            secure=False
        )
        response.set_cookie(
            'refresh_token', 
            str(refresh_token), 
            httponly=True, 
            samesite='Lax',
            max_age=86400,
            secure=False
        )
    
    def post(self, request, *args, **kwargs):
        """Handles user login"""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not self._validate_login_credentials(username, password):
            return Response({
                "detail": "Username und Passwort sind erforderlich."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = self._authenticate_user(username, password)
        
        if user is None:
            return Response({
                "detail": "Ungültige Anmeldedaten."
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh_token = RefreshToken.for_user(user)
        response = self._create_login_response(user, refresh_token)
        self._set_auth_cookies(response, refresh_token)
        
        return response


@method_decorator(csrf_exempt, name='dispatch')
class UserLogoutView(GenericAPIView):
    """View for user logout"""
    permission_classes = [IsAuthenticated]
    
    def _blacklist_access_token(self, access_token):
        """Blacklists access token"""
        if not access_token:
            return
        
        try:
            token = AccessToken(access_token)
            jti = token.payload.get('jti')
            if jti:
                BlacklistedToken.objects.get_or_create(
                    token__jti=jti, 
                    defaults={'token': token}
                )
        except Exception:
            pass
    
    def _blacklist_refresh_token(self, refresh_token):
        """Blacklists refresh token"""
        if not refresh_token:
            return
        
        try:
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()
        except Exception:
            pass
    
    def _blacklist_header_token(self, request):
        """Blacklists token from Authorization header"""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return
        
        try:
            token_string = auth_header.split(' ')[1]
            token = AccessToken(token_string)
            jti = token.payload.get('jti')
            if jti:
                BlacklistedToken.objects.get_or_create(
                    token__jti=jti, 
                    defaults={'token': token}
                )
        except Exception:
            pass
    
    def _create_logout_response(self):
        """Creates logout response"""
        response = Response({
            "detail": "Log-Out successfully! All tokens have been invalidated."
        }, status=status.HTTP_200_OK)
        
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        
        return response
    
    def post(self, request, *args, **kwargs):
        """Handles user logout"""
        try:
            access_token = request.COOKIES.get('access_token')
            refresh_token = request.COOKIES.get('refresh_token')
            
            self._blacklist_access_token(access_token)
            self._blacklist_refresh_token(refresh_token)
            self._blacklist_header_token(request)
            
            return self._create_logout_response()
            
        except Exception as e:
            return Response({
                "detail": f"Fehler beim Logout: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class TokenValidationView(GenericAPIView):
    """View for token validation"""
    permission_classes = [AllowAny]
    
    def _get_access_token(self, request):
        """Gets access token from request"""
        access_token = request.COOKIES.get('access_token')
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]
        
        return access_token
    
    def _validate_token(self, access_token):
        """Validates access token"""
        if not access_token:
            return None, "Kein Token gefunden"
        
        try:
            token = AccessToken(access_token)
            user_id = token.payload.get('user_id')
            user = User.objects.get(id=user_id)
            return user, token
        except Exception as e:
            return None, f"Token ungültig: {str(e)}"
    
    def get(self, request, *args, **kwargs):
        """Validates current authentication status"""
        access_token = self._get_access_token(request)
        user, token_or_error = self._validate_token(access_token)
        
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
    
    def _get_refresh_token(self, request):
        """Gets refresh token from request"""
        return request.COOKIES.get('refresh_token')
    
    def _refresh_access_token(self, refresh_token):
        """Refreshes access token"""
        if not refresh_token:
            return None, "Refresh token fehlt."
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return access_token, None
        except Exception:
            return None, "Ungültiger Refresh Token."
    
    def _create_refresh_response(self, access_token):
        """Creates refresh response with new token"""
        response = Response({
            "detail": "Token refreshed",
            "access_token": access_token
        }, status=status.HTTP_200_OK)
        
        response.set_cookie(
            'access_token', 
            access_token, 
            httponly=True, 
            samesite='Lax',
            max_age=3600,
            secure=False
        )
        
        return response
    
    def post(self, request, *args, **kwargs):
        """Handles token refresh"""
        refresh_token = self._get_refresh_token(request)
        access_token, error = self._refresh_access_token(refresh_token)
        
        if access_token is None:
            return Response({
                "detail": error
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return self._create_refresh_response(access_token)