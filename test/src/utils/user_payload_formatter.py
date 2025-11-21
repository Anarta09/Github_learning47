from schemas.user_schema import UserCreateRequest, UserAttributesRequest


def format_user_payload(user: UserCreateRequest) -> dict:
    """
    Format user creation payload for Keycloak.
    """
    return {
        "username": user.username,
        "email": user.email,
        "enabled": user.enabled,
        "firstName": user.firstName,
        "lastName": user.lastName,
        "emailVerified": True,
        "credentials": [
            {
                "type": "password",
                "value": user.password,
                "temporary": False,
            }
        ],
    }


def format_user_attributes(attrs: UserAttributesRequest) -> dict:
    """
    Format user attributes payload for Keycloak.
    """
    return {
        "user_role": attrs.user_role,
        "kc_client": attrs.kc_client,
        "user_org_id": str(attrs.user_org_id),
        "user_full_name": attrs.user_full_name,
        "user_client_name": attrs.user_client_name,
        "client_ids": attrs.client_ids or [],
    }
