from pydantic_settings import BaseSettings
from pydantic import Field
from keycloak import KeycloakOpenID

KEYCLOAK_SERVER_URL="https://localhost:8080/auth"
KEYCLOAK_REALM="interview-coach-realm"
KEYCLOAK_CLIENT_ID="interview-coach-client"
KEYCLOAK_CLIENT_SECRET="njzA7IqVXx5twcxms7gsRGCnmyya0g3V"

class Settings(BaseSettings):
    keycloak_server_url: str = KEYCLOAK_SERVER_URL
    keycloak_realm: str = KEYCLOAK_REALM
    keycloak_client_id: str = KEYCLOAK_CLIENT_ID
    keycloak_client_secret: str = KEYCLOAK_CLIENT_SECRET

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

keycloak_openid = KeycloakOpenID(
    server_url=settings.keycloak_server_url,
    realm_name=settings.keycloak_realm,
    client_id=settings.keycloak_client_id,
    client_secret_key=settings.keycloak_client_secret,
)

def get_openid_config():
    return keycloak_openid.well_known()