from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import TokenResponse, UserInfo
from authentication.auth_service import AuthService
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize HTTPBearer security dependency
bearer_scheme = HTTPBearer()


class AuthController:
    """
    Controller for handling authentication logic.
    """

    @staticmethod
    def read_root():
        """
        Root endpoint providing basic information and documentation link.

        Returns:
            dict: A welcome message and link to the documentation.
        """
        return { "message": (
                "Welcome to the Keycloak authentication system. "
                "Use the /login endpoint to authenticate and /protected to access the protected resource."
            )
        }
    
    @staticmethod
    def login(email: str, password: str) -> TokenResponse:
        """
        Authenticate user and return access and refresh tokens.
        """
        try:
            logger.info(f"Login attempt for user: {email}")
            tokens = AuthService.authenticate_user(email, password)
            if not tokens or not tokens.get("access_token"):
                logger.error(f"Login failed for user {email}: No access token returned")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password",
                )
            logger.info(f"Login successful for user: {email}")
            return TokenResponse(access_token=tokens["access_token"], refresh_token=tokens.get("refresh_token"))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @staticmethod
    def protected_endpoint(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    ) -> UserInfo:
        """
        Access a protected resource that requires valid token authentication.

        Args:
            credentials (HTTPAuthorizationCredentials): Bearer token provided via HTTP Authorization header.

        Raises:
            HTTPException: If the token is invalid or not provided.

        Returns:
            UserInfo: Information about the authenticated user.
        """
        try:
            logger.info("Protected endpoint accessed")
            # Extract the bearer token from the provided credentials
            token = credentials.credentials

            # Verify the token and get user information
            user_info = AuthService.verify_token(token)

            if not user_info:
                logger.error("Protected endpoint: Invalid token - no user info returned")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            logger.info(f"Protected endpoint: Successfully verified token for user: {user_info.email}")
            return user_info
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in protected endpoint: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @staticmethod
    def register(email: str, password: str, first_name: str, last_name: str) -> TokenResponse:
        """
        Register a new user and return access and refresh tokens.
        """
        try:
            logger.info(f"Registration attempt for user: {email}")
            logger.info("Calling AuthService.register_user")
            try:
                tokens = AuthService.register_user(email, password, first_name, last_name)
                logger.info("AuthService.register_user completed successfully")
            except Exception as auth_error:
                logger.error(f"AuthService.register_user failed: {str(auth_error)}", exc_info=True)
                raise
            if not tokens or not tokens.get("access_token"):
                logger.error("Registration failed: No access token returned")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to register user",
                )
            logger.info(f"Registration successful for user: {email}")
            return TokenResponse(access_token=tokens["access_token"], refresh_token=tokens.get("refresh_token"))
        except HTTPException as he:
            logger.error(f"HTTP error during registration: {str(he)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @staticmethod
    def refresh(refresh_token: str) -> TokenResponse:
        """
        Refresh the access token using the provided refresh token.
        """
        try:
            tokens = AuthService.refresh_access_token(refresh_token)
            if not tokens or not tokens.get("access_token"):
                logger.error("Refresh failed: No access token returned")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token",
                )
            logger.info("Token refresh successful")
            return TokenResponse(access_token=tokens["access_token"], refresh_token=tokens.get("refresh_token"))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    