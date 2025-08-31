from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .serializers import UserRegistrationSerializer, UserSerializer


class UserRegistrationView(CreateAPIView):
    """
    View für die Benutzerregistrierung
    """
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
    """
    View für die Benutzeranmeldung
    """
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
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)
        
        response.set_cookie('access_token', str(refresh.access_token), httponly=True, samesite='Lax')
        response.set_cookie('refresh_token', str(refresh), httponly=True, samesite='Lax')
        
        return response


@method_decorator(csrf_exempt, name='dispatch')
class UserLogoutView(GenericAPIView):
    """
    View für die Benutzerabmeldung
    """
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
                except Exception as e:
                    print(f"Fehler beim Blacklisten des Access-Tokens aus Cookies: {e}")
            
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                try:
                    refresh = RefreshToken(refresh_token)
                    refresh.blacklist()
                except Exception as e:
                    print(f"Fehler beim Blacklisten des Refresh-Tokens aus Cookies: {e}")
            
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
                except Exception as e:
                    print(f"Fehler beim Blacklisten des Access-Tokens aus Header: {e}")
            
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


class TokenRefreshView(GenericAPIView):
    """
    View für das Erneuern von Access-Tokens
    """
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
                "access": access_token
            }, status=status.HTTP_200_OK)
            
            response.set_cookie('access_token', access_token, httponly=True, samesite='Lax')
            
            return response
        except Exception as e:
            return Response({
                "detail": "Ungültiger Refresh Token."
            }, status=status.HTTP_401_UNAUTHORIZED)
