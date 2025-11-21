## unassign/assign roles API payload:

[
  {
    "source": "realm",
    "clientId": null,
    "name": "offline_access",
    "description": "${role_offline-access}"
  },
  {
    "source": "realm",
    "clientId": null,
    "name": "uma_authorization",
    "description": "${role_uma_authorization}"
  },
  {
    "source": "client",
    "clientId": "account",
    "name": "view-profile",
    "description": "${role_view-profile}"
  },
  {
    "source": "client",
    "clientId": "realm-management",
    "name": "manage-users",
    "description": "${role_manage-users}"
  },
  {
    "source": "client",
    "clientId": "AnnovaHealthCare",
    "name": "test-admin",
    "description": ""
  }
]


## create bulk protocol mappers:
[
  {
    "name": "username_mapper",
    "protocol": "openid-connect",
    "protocolMapper": "oidc-usermodel-property-mapper",
    "consentRequired": false,
    "config": {
      "userinfo.token.claim": "true",
      "user.attribute": "username",
      "id.token.claim": "true",
      "access.token.claim": "true",
      "claim.name": "preferred_username",
      "jsonType.label": "String"
    }
  },
  {
    "name": "email_mapper",
    "protocol": "openid-connect",
    "protocolMapper": "oidc-usermodel-property-mapper",
    "config": {
      "user.attribute": "email",
      "claim.name": "email",
      "jsonType.label": "String",
      "id.token.claim": "true"
    }
  }
]
