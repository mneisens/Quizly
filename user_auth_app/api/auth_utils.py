from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User


def validate_login_credentials(username, password):
    """Validates login credentials"""
    if not username or not password:
        return False
    return True


def authenticate_user(username, password):
    """Authenticates user with credentials"""
    return authenticate(username=username, password=password)


def create_refresh_token_for_user(user):
    """Creates refresh token for user"""
    return RefreshToken.for_user(user)


def create_login_response_data(user, refresh_token):
    """Creates login response data"""
    from .serializers import UserSerializer
    
    return {
        "detail": "Login successfully!",
        "user": UserSerializer(user).data,
        "access_token": str(refresh_token.access_token),
        "refresh_token": str(refresh_token)
    }


def set_auth_cookies(response, refresh_token):
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
        max_age=604800,
        secure=False
    )


def blacklist_access_token(access_token):
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


def blacklist_refresh_token(refresh_token):
    """Blacklists refresh token"""
    if not refresh_token:
        return
    
    try:
        refresh = RefreshToken(refresh_token)
        refresh.blacklist()
    except Exception:
        pass


def blacklist_header_token(request):
    """Blacklists token from Authorization header"""
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if auth_header and auth_header.startswith('Bearer '):
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


def get_access_token_from_request(request):
    """Gets access token from request"""
    access_token = request.COOKIES.get('access_token')
    if not access_token:
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]
    return access_token


def validate_access_token(access_token):
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


def get_refresh_token_from_request(request):
    """Gets refresh token from request"""
    return request.COOKIES.get('refresh_token')


def refresh_access_token(refresh_token):
    """Refreshes access token"""
    if not refresh_token:
        return None, "Refresh token fehlt."
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        return access_token, None
    except Exception:
        return None, "Ungültiger Refresh Token."


def create_refresh_response_data(access_token):
    """Creates refresh response data"""
    return {
        "detail": "Token refreshed",
        "access_token": access_token
    }


def set_refresh_cookie(response, access_token):
    """Sets refresh cookie"""
    response.set_cookie(
        'access_token', 
        access_token, 
        httponly=True, 
        samesite='Lax',
        max_age=3600,
        secure=False
    )


def normalize_registration_data(data):
    """Normalizes registration data"""
    normalized_data = data.copy()
    if 'email' in normalized_data:
        normalized_data['email'] = normalized_data['email'].lower().strip()
    return normalized_data


def validate_password_match(password, password2):
    """Validates password match"""
    if password != password2:
        raise ValueError("Passwörter stimmen nicht überein.")


def remove_password2_from_data(validated_data):
    """Removes password2 from validated data"""
    validated_data.pop('password2', None)
    return validated_data
