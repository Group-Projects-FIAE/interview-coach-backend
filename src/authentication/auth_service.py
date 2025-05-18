from fastapi import HTTPException, status
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError
from keycloak.keycloak_admin import KeycloakAdmin
from keycloak.keycloak_openid import KeycloakOpenID
from keycloak.connection import ConnectionManager
import requests
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from .auth_config import settings
from models import UserInfo

class CustomConnection(ConnectionManager):
    def __init__(self, base_url, headers=None, timeout=60):
        super().__init__(base_url, headers, timeout)
        self._token = None
        self.realm_name = settings.keycloak_realm  # Add realm_name attribute
        logger.debug(f"CustomConnection initialized with base_url: {base_url} and realm: {self.realm_name}")

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        logger.debug("Setting new token in CustomConnection")
        self._token = value
        if value:
            self.headers["Authorization"] = f"Bearer {value}"
            logger.debug("Authorization header set")
        elif "Authorization" in self.headers:
            del self.headers["Authorization"]
            logger.debug("Authorization header removed")

def get_admin_token():
    """Get admin token using direct API call"""
    try:
        logger.info("Attempting to get admin token")
        data = {
            'client_id': 'admin-cli',
            'grant_type': 'password',
            'username': settings.keycloak_admin_username,
            'password': settings.keycloak_admin_password
        }
        
        token_url = f"{settings.keycloak_server_url}/realms/master/protocol/openid-connect/token"
        logger.debug(f"Token URL: {token_url}")
        
        response = requests.post(token_url, data=data)
        logger.debug(f"Token response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Failed to get admin token. Status: {response.status_code}, Response: {response.text}")
            raise Exception(f"Failed to get admin token: {response.text}")
            
        token_data = response.json()
        logger.info("Successfully obtained admin token")
        return token_data  # Return the full token dict
    except Exception as e:
        logger.error(f"Failed to get admin token: {str(e)}", exc_info=True)
        raise

# Initialize variables at module level
keycloak_admin = None
keycloak_openid = None
admin_token = None

def initialize_keycloak():
    """Initialize both KeycloakAdmin and KeycloakOpenID clients"""
    global keycloak_admin, keycloak_openid, admin_token
    
    logger.info("Initializing Keycloak clients...")
    
    try:
        # First initialize OpenID client as it's critical for basic auth
        keycloak_openid = KeycloakOpenID(
            server_url=settings.keycloak_server_url,
            realm_name=settings.keycloak_realm,
            client_id=settings.keycloak_client_id,
            client_secret_key=settings.keycloak_client_secret
        )
        logger.info("KeycloakOpenID initialized successfully")
        
        # Then try to initialize admin client
        admin_token = get_admin_token()
        keycloak_admin = KeycloakAdmin(
            server_url=settings.keycloak_server_url,
            username=settings.keycloak_admin_username,
            password=settings.keycloak_admin_password,
            realm_name=settings.keycloak_realm,
            verify=True
        )
        logger.info("KeycloakAdmin initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Keycloak clients: {str(e)}", exc_info=True)
        if not keycloak_openid:
            # If OpenID client failed to initialize, we should raise as it's critical
            raise
        # If only admin client failed, we can continue with limited functionality
        logger.warning("Application will start with limited administrative functionality")
        return False

# Initialize Keycloak clients on module load
initialize_keycloak()

class AuthService:
    @staticmethod
    def authenticate_user(email: str, password: str) -> dict:
        """
        Authenticate the user using Keycloak and return access and refresh tokens.
        """
        if not keycloak_openid:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service is currently unavailable"
            )
        try:
            logger.info(f"Attempting to authenticate user: {email}")
            token = keycloak_openid.token(
                grant_type=["password"],
                username=email,
                password=password
            )
            logger.info("User authenticated successfully")
            return {
                "access_token": token.get("access_token"),
                "refresh_token": token.get("refresh_token")
            }
        except KeycloakAuthenticationError as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        
    @staticmethod
    def verify_token(token: str) -> UserInfo:
        """
        Verify the given token and return user information.
        """
        try:
            logger.info("Attempting to verify token")
            user_info = keycloak_openid.userinfo(token)
            logger.debug(f"User info received: {user_info}")
            if not user_info:
                logger.error("No user info returned")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )
            return UserInfo(
                preferred_username=user_info.get("preferred_username") or user_info.get("email"),
                email=user_info.get("email"),
                full_name=user_info.get("name"),
            )
        except KeycloakAuthenticationError as e:
            logger.error(f"Token verification error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    @staticmethod
    def register_user(email: str, password: str, first_name: str, last_name: str) -> dict:
        """
        Register a new user using Keycloak.
        """
        if not keycloak_admin:
            logger.error("KeycloakAdmin not initialized, attempting to initialize...")
            if not initialize_keycloak():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Registration service is currently unavailable"
                )

        try:
            logger.info(f"Attempting to create user with email: {email}")
            
            # Create user in Keycloak using admin client
            user_data = {
                "email": email,
                "username": email,
                "enabled": True,
                "firstName": first_name,
                "lastName": last_name,
                "credentials": [{
                    "type": "password",
                    "value": password,
                    "temporary": False
                }],
                "requiredActions": [],
                "emailVerified": True  # Skip email verification for now
            }
            logger.debug(f"User data to be created: {user_data}")
            
            try:
                # Get a fresh admin token and update connection
                logger.info("Getting fresh admin token")
                admin_token = get_admin_token()  # Now a dict
                keycloak_admin.connection.token = admin_token  # Set the full dict
                
                # Create user using admin client
                logger.info("Attempting to create user in Keycloak")
                try:
                    user_id = keycloak_admin.create_user(user_data)
                    logger.info(f"User created with ID: {user_id}")
                except KeycloakGetError as ke:
                    logger.error(f"Keycloak error creating user: {str(ke)}")
                    if "409" in str(ke):  # Conflict - user already exists
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="User with this email already exists"
                        )
                    raise
                except Exception as e:
                    logger.error(f"Error creating user: {str(e)}", exc_info=True)
                    raise
            except Exception as create_error:
                logger.error(f"Error in user creation process: {str(create_error)}", exc_info=True)
                raise

            if not user_id:
                logger.error("Failed to create user: No user ID returned")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create user"
                )

            # Add a retry mechanism for token acquisition
            max_retries = 3
            retry_delay = 1  # seconds
            last_error = None

            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempting to get token for new user (attempt {attempt + 1}/{max_retries})")
                    # Get token for the new user
                    token = keycloak_openid.token(
                        grant_type=["password"],
                        username=email,
                        password=password
                    )
                    logger.info("Token successfully obtained for new user")
                    return {
                        "access_token": token.get("access_token"),
                        "refresh_token": token.get("refresh_token")
                    }
                except Exception as token_error:
                    last_error = token_error
                    logger.warning(f"Token acquisition attempt {attempt + 1} failed: {str(token_error)}")
                    if attempt < max_retries - 1:
                        logger.info(f"Waiting {retry_delay} seconds before next attempt")
                        time.sleep(retry_delay)
                    continue

            # If we get here, all retries failed
            logger.error(f"Failed to get token after {max_retries} attempts: {str(last_error)}")
            raise last_error

        except KeycloakAuthenticationError as e:
            logger.error(f"Keycloak authentication error: {str(e)}")
            logger.error(f"Error details: {e.__dict__}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
            logger.error(f"Error type: {type(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )

    @staticmethod
    def refresh_access_token(refresh_token: str) -> dict:
        """
        Use the refresh token to obtain a new access token from Keycloak.
        """
        if not keycloak_openid:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service is currently unavailable"
            )
        try:
            logger.info("Attempting to refresh access token using refresh token")
            token = keycloak_openid.token(
                grant_type=["refresh_token"],
                refresh_token=refresh_token
            )
            logger.info("Access token refreshed successfully")
            return {
                "access_token": token.get("access_token"),
                "refresh_token": token.get("refresh_token")
            }
        except Exception as e:
            logger.error(f"Failed to refresh access token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )