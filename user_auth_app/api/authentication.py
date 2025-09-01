from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
import logging

logger = logging.getLogger(__name__)


class CookieJWTAuthentication(JWTAuthentication):
    """
    Authentifizierung über JWT-Tokens in Cookies
    """
    
    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                try:
                    validated_token = self.get_validated_token(raw_token)
                    return self.get_user(validated_token), validated_token
                except (InvalidToken, TokenError) as e:
                    logger.warning(f"Invalid token in header: {e}")
                    return None
        
        access_token = request.COOKIES.get('access_token')
        if access_token:
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
        
        logger.debug("No valid token found in header or cookies")
        return None
