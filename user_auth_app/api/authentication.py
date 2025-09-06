from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
import logging

logger = logging.getLogger(__name__)


class CookieJWTAuthentication(JWTAuthentication):
    """Authentication using JWT tokens in cookies"""
    
    def _authenticate_from_header(self, request):
        """Authenticates user from Authorization header"""
        header = self.get_header(request)
        if header is None:
            return None
        
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Invalid token in header: {e}")
            return None
    
    def _authenticate_from_cookie(self, request):
        """Authenticates user from access token cookie"""
        access_token = request.COOKIES.get('access_token')
        if not access_token:
            return None
        
        try:
            validated_token = self.get_validated_token(access_token)
            user = self.get_user(validated_token)
            logger.info(f"Successfully authenticated user: {user.username}")
            return user, validated_token
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Invalid token in cookie: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return None
    
    def authenticate(self, request):
        """Main authentication method"""
        header_auth = self._authenticate_from_header(request)
        if header_auth:
            return header_auth
        
        cookie_auth = self._authenticate_from_cookie(request)
        if cookie_auth:
            return cookie_auth
        
        logger.debug("No valid token found in header or cookies")
        return None