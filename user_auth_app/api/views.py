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
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if 'confirmed_password' in data:
            data['password2'] = data.pop('confirmed_password')
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "detail": "User created successfully!"
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                "detail": "Username und Passwort sind erforderlich."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return Response({
                "detail": "Ungültige Anmeldedaten."
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh = RefreshToken.for_user(user)
        
        response = Response({
            "detail": "Login successfully!",
            "user": UserSerializer(user).data,
            "access_token": str(refresh.access_token),  # Token auch in Response für Frontend
            "refresh_token": str(refresh)
        }, status=status.HTTP_200_OK)
        
        # Verbesserte Cookie-Einstellungen
        response.set_cookie(
            'access_token', 
            str(refresh.access_token), 
            httponly=True, 
            samesite='Lax',
            max_age=3600,  # 1 Stunde
            secure=False   # Für Entwicklung auf False
        )
        response.set_cookie(
            'refresh_token', 
            str(refresh), 
            httponly=True, 
            samesite='Lax',
            max_age=86400,  # 1 Tag
            secure=False    # Für Entwicklung auf False
        )
        
        return response


@method_decorator(csrf_exempt, name='dispatch')
class UserLogoutView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            access_token = request.COOKIES.get('access_token')
            if access_token:
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
            
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                try:
                    refresh = RefreshToken(refresh_token)
                    refresh.blacklist()
                except Exception:
                    pass
            
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
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


class TestAuthView(GenericAPIView):
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """Einfache Test-View ohne Authentifizierung"""
        return Response({
            "message": "Test-View funktioniert!",
            "method": request.method,
            "cookies_count": len(request.COOKIES),
            "has_access_token": 'access_token' in request.COOKIES,
            "has_refresh_token": 'refresh_token' in request.COOKIES,
        }, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        """Test-POST ohne Authentifizierung"""
        return Response({
            "message": "POST funktioniert!",
            "data_received": request.data,
            "cookies": list(request.COOKIES.keys()),
        }, status=status.HTTP_200_OK)


class ProtectedTestView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Geschützte View mit Authentifizierung"""
        return Response({
            "message": "Geschützte View funktioniert!",
            "user": request.user.username,
            "user_id": request.user.id,
            "is_authenticated": request.user.is_authenticated,
        }, status=status.HTTP_200_OK)


class DebugAuthView(GenericAPIView):
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """Debug-View für Authentifizierungsprobleme"""
        cookies = request.COOKIES
        headers = dict(request.META)
        
        # Filter sensitive headers
        sensitive_headers = ['HTTP_AUTHORIZATION', 'HTTP_COOKIE']
        filtered_headers = {k: v for k, v in headers.items() if k not in sensitive_headers}
        
        return Response({
            "cookies": cookies,
            "headers": filtered_headers,
            "user_agent": request.META.get('HTTP_USER_AGENT'),
            "origin": request.META.get('HTTP_ORIGIN'),
            "referer": request.META.get('HTTP_REFERER'),
            "method": request.method,
            "path": request.path,
        }, status=status.HTTP_200_OK)


class TokenValidationView(GenericAPIView):
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """Überprüft den aktuellen Authentifizierungsstatus"""
        access_token = request.COOKIES.get('access_token')
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]
        
        if not access_token:
            return Response({
                "authenticated": False,
                "detail": "Kein Token gefunden"
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            token = AccessToken(access_token)
            user_id = token.payload.get('user_id')
            user = User.objects.get(id=user_id)
            
            return Response({
                "authenticated": True,
                "user": UserSerializer(user).data,
                "token_exp": token.payload.get('exp')
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "authenticated": False,
                "detail": f"Token ungültig: {str(e)}"
            }, status=status.HTTP_401_UNAUTHORIZED)


class TokenRefreshView(GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response({
                "detail": "Refresh token fehlt."
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
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
        except Exception as e:
            return Response({
                "detail": "Ungültiger Refresh Token."
            }, status=status.HTTP_401_UNAUTHORIZED)
