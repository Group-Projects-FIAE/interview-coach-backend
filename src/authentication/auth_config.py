from keycloak.keycloak_openid import KeycloakOpenID
from pydantic_settings import BaseSettings
import os
import time
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    keycloak_server_url: str
    keycloak_realm: str
    keycloak_client_id: str
    keycloak_client_secret: str
    keycloak_admin_username: str
    keycloak_admin_password: str

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"  # This will ignore extra fields in the .env file

settings = Settings()

print("Keycloak Configuration:")
print(f"Server URL: {settings.keycloak_server_url}")
print(f"Realm: {settings.keycloak_realm}")
print(f"Client ID: {settings.keycloak_client_id}")
print(f"Admin Username: {settings.keycloak_admin_username}")
print(f"Environment file location: {os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')}")

def init_keycloak(max_retries=1):
    """Initialize Keycloak with retry mechanism"""
    retry_count = 0
    while retry_count < max_retries:
        try:
            keycloak_openid = KeycloakOpenID(
                server_url=settings.keycloak_server_url,
                realm_name=settings.keycloak_realm,
                client_id=settings.keycloak_client_id,
                client_secret_key=settings.keycloak_client_secret,
                verify=True
            )
            
            # Test the connection
            public_key = keycloak_openid.public_key()
            print("KeycloakOpenID initialized successfully")
            return keycloak_openid
            
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                print(f"Failed to initialize Keycloak (attempt {retry_count}). Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print(f"Error initializing KeycloakOpenID: {str(e)}")
                # Return None instead of raising an exception
                return None

# Initialize Keycloak with a single retry
keycloak_openid = init_keycloak(max_retries=1)

def get_openid_config():
    try:
        config = keycloak_openid.well_known()
        print("Successfully retrieved OpenID configuration")
        return config
    except Exception as e:
        print(f"Error getting OpenID configuration: {str(e)}")
        raise
