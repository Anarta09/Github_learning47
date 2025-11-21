import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    log_level: str = "INFO"

    KEYCLOAK_BASE_URL = os.getenv(
        "KEYCLOAK_BASE_URL",
        "",
    )
    KEYCLOAK_ISSUER = os.getenv(
        "KEYCLOAK_ISSUER",
        "",
    )

    RESOURCE_ASSIGNMENT_URL = f"{KEYCLOAK_BASE_URL}/admin"

    AUTH_URL = f"{KEYCLOAK_ISSUER}/protocol/openid-connect/auth"
    TOKEN_URL = f"{KEYCLOAK_ISSUER}/protocol/openid-connect/token"
    JWKS_URL = f"{KEYCLOAK_ISSUER}/protocol/openid-connect/certs"

    REALM = os.getenv("KEYCLOAK_REALM", "")
    CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "")
    CLIENT_SECRET = os.getenv(
        "KEYCLOAK_CLIENT_SECRET", ""
    )
    REDIRECT_URI = os.getenv("KEYCLOAK_REDIRECT_URI", "")

    ADMIN_URL = f"{KEYCLOAK_BASE_URL}/admin/realms/{REALM}"

    TEMPLATE_FILE = ""
    OUTPUT_DIR = ""

    POSTGRES_DATABASE_URL: str = os.getenv(
        "POSTGRES_URL",
        ""
    )

    DEFAULT_REDIRECT_URI = ""


settings = Settings()
