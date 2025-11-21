from fastapi import HTTPException
from fastapi.responses import JSONResponse
import status

# ==========================
# Error Constants
# ==========================
class ErrorException:
    # ------------------- Authentication / Token Errors -------------------
    ERROR_ADMIN_TOKEN_FETCH = "Failed to retrieve admin token. Please try again or contact support if the issue persists."
    INVALID_ADMIN_TOKEN = "Admin token is invalid or expired. Please login again."

    # ------------------- Client Fetch / Search Errors -------------------
    KEYCLOAK_CLIENTS_FETCH_FAILED = "Failed to fetch clients from Keycloak. Please try again or contact support if the issue persists."
    KEYCLOAK_CONNECTION_ERROR = "Unable to connect to Keycloak server. Please check the connection or try again later."
    KEYCLOAK_RESPONSE_INVALID = "Keycloak returned invalid or malformed client data. Please contact support if the issue persists."
    CLIENT_SEARCH_NO_RESULTS = "No clients found matching the search criteria. Please check the search term and try again."

    # ------------------- Client Creation / Reactivation Errors -------------------
    CLIENT_ALREADY_ACTIVE = "Client already exists and is active. Skipping creation."
    CLIENT_CREATION_FAILED = "Failed to create client in Keycloak. Please try again or contact support if the issue persists."
    CLIENT_UUID_FETCH_FAILED = "Failed to fetch client UUID after creation. Please try again or contact support if the issue persists."
    ERROR_FETCHING_EXISTING_CLIENTS = "Failed to fetch existing clients from Keycloak. Please try again or contact support if the issue persists."
    ERROR_PREPARING_CLIENT_PAYLOAD = "An unexpected error occurred while preparing the client payload for processing"
    ERROR_FETCHING_DB_CLIENT = "An unexpected error occurred while retrieving the client details from the database"
    ERROR_CREATING_DB_CLIENT="Failed to fetch existing Keycloak clients. Please try again or contact support if the issue persists."
    ERROR_IMPORTING_RESOURCES="An unexpected error occurred during the resource import process. "
    ERROR_PROCESSING_SINGLE_CLIENT="An unexpected error occurred while processing the client.Please try again or contact support if the issue persists."
    DB_SAVE_CLIENT_FAILED = "Failed to save client details to the database. Please try again or contact support if the issue persists."
    DB_REACTIVATE_CLIENT_FAILED = "Failed to reactivate client in the database. Please try again or contact support if the issue persists."
    CLIENT_RESOURCE_IMPORT_FAILED = "Failed to import resources from another client. Please try again or contact support if the issue persists."
    KEYCLOAK_CLIENT_DELETE_FAILED = "Failed to delete the client from Keycloak. Please verify the client ID and try again."
    DB_INSERT_FAILED="The system encountered an unexpected error while attempting to insert data ."
    KEYCLOAK_POLICY_CREATE_FAILED="Failed to create policy.Please try again or contact support if the issue persists."
    KEYCLOAK_POLICY_DELETE_FAILED="Failed to delete policy.Please try again or contact support if the issue persists."
    INVALID_INPUT="The input provided is invalid or does not meet the required format or constraints. "
    # ------------------- Client Deletion Errors -------------------
    CLIENT_NOT_FOUND_KEYCLOAK = "Client not found in Keycloak. Please verify the client ID."
    CLIENT_NOT_FOUND_DB = "Client not found in the database or already inactive."
    CLIENT_DB_DEACTIVATE_FAILED = "Failed to deactivate client in the database. Please try again or contact support if the issue persists."
    CLIENT_KEYCLOAK_DELETE_FAILED = "Failed to delete client from Keycloak. Please try again or contact support if the issue persists."
    KEYCLOAK_RESPONSE_INVALID_DELETE = "Keycloak returned an unexpected response while deleting client. Please contact support if the issue persists."
    ERROR_FETCHING_CLIENT_UUID = "An unexpected error occurred while retrieving the client UUID from the system"

    ROLE_PROCESSING_FAILED="An unexpected error occurred while processing roles.Please try again or contact support if the issue persists."
    ROLES_CREATION_FAILED="Failed to create roles. Please try again or contact support if the issue persists."
    KEYCLOAK_ROLE_DELETE_FAILED="Failed to delete roles. Please try again or contact support if the issue persists."
    # ------------------- Source Client Errors -------------------
    SOURCE_CLIENT_NOT_FOUND = "Source client not found in Keycloak. Please verify the client ID."
    SOURCE_CLIENT_UUID_FETCH_FAILED = "Failed to fetch UUID for the source client. Please try again or contact support if the issue persists."

    # ------------------- Resource Fetching Errors -------------------
    RESOURCE_FETCH_FAILED = "Failed to fetch resources from Keycloak for the client. Please try again or contact support if the issue persists."
    SCOPE_FETCH_FAILED = "Failed to fetch scopes from Keycloak for the client. Please try again or contact support if the issue persists."
    POLICY_FETCH_FAILED = "Failed to fetch policies from Keycloak for the client. Please try again or contact support if the issue persists."
    PERMISSION_FETCH_FAILED = "Failed to fetch permissions from Keycloak for the client. Please try again or contact support if the issue persists."

    # ------------------- Resource Import Errors -------------------
    RESOURCE_IMPORT_FAILED = "Failed to import resources into the target client. Please try again or contact support if the issue persists."
    RESOURCE_POST_FAILED = "Failed to POST resource to Keycloak. Please verify the data and try again."
    RESOURCE_ALREADY_EXISTS = "Resource already exists in Keycloak. Skipping import."
    RESOURCE_NAME_MISSING = "Resource name missing. Cannot import resource without a name."

    # ------------------- Thread / Worker Errors -------------------
    THREAD_WORKER_EXCEPTION = "Exception occurred in resource import worker thread. Please check logs for details."

    # ------------------- General / Fallback Errors -------------------
    INTERNAL_SERVER_ERROR = "An unexpected error occurred. Please try again or contact support if the issue persists."
    

    # Client-related errors
    CLIENT_ALREADY_ACTIVE = "Client is already active."
    CLIENT_CREATION_FAILED = "Failed to create client in Keycloak."
    CLIENT_UUID_FETCH_FAILED = "Failed to fetch UUID for the created client."
    CLIENT_RESOURCE_IMPORT_FAILED = "Failed to import resources for the client."
    LIST_ROLES_FAILED="The system encountered an unexpected error while attempting to retrieve the list "
    ROLE_NOT_FOUND="Role id  not found while logging action.Please try again or contact support if the error persists."
    # DB or general errors
    CLIENT_NOT_FOUND = "Client not found."
    DATABASE_ERROR = "Database operation failed."

    # ---- Database Operation Errors ----
    DB_SAVE_ERROR = "Database error occurred while saving ."
    DB_UPDATE_ERROR = "Database error occurred while updating ."

    CLIENT_SCOPE_DELETE_FAILED = "Failed to delete client-specific scopes from Keycloak"
    UNEXPECTED_ERROR="An unexpected error has occured .Please try again or contact support if the error persists."

class Messages:
    """Centralized messages to avoid hardcoding in services"""

    # ------------------ Client Service ------------------
    CLIENT_SERVICE_INIT_FAILED = "ClientService initialization failed"
    ADMIN_TOKEN_UNAVAILABLE = "Admin token is unavailable or could not be retrieved. Please login again or contact support."
    CLIENTS_FETCH_FAILED = "Unable to retrieve clients. Please try again or contact support if the issue persists."




    # ------------------ HTTP Request / Keycloak ------------------
    KEYCLOAK_CONNECTION_FAILED = "Keycloak connection failed"
    SAFE_REQUEST_EXECUTION_FAILED = "Safe request execution failed"
    CLIENTSERVICE_INIT_FAILED = "Failed to initialize ClientService. Please check the configuration or contact support."
    KEYCLOAK_CLIENTS_REQUEST_FAILED = "Unable to fetch clients from Keycloak."
    CLIENTS_EXISTING_FETCH_FAILED = "Failed to fetch existing clients"
    CLIENT_CREATION_FAILED="Failed to create Keycloak client"
    CLIENT_UUID_FETCH_FAILED="Failed to fetch client UUID after retries"
    SOURCE_CLIENT_NOT_FOUND="Source client not found"
    ERROR_FETCHING_CLIENT_UUID="Failed to fetch client UUID"
    RESOURCE_FETCH_FAILED="Failed to fetch client resources"
    KEYCLOAK_CLIENTS_FETCH_FAILED = "Failed to fetch clients from Keycloak"
    CLIENTS_NOT_FOUND = "No matching clients found"
    CLIENT_LOG_FAILED = "Failed to save client action log. Please try again or contact support if the issue persists."
    CLIENTS_NO_MATCH = "No clients found matching the search criteria. Please check your input and try again."
    KEYCLOAK_CLIENT_DELETE_FAILED = "Failed to delete the client from Keycloak. Please verify the client ID and try again."
    ERROR_CREATING_DB_CLIENT="Failed to create client in database"
    CLIENT_NOT_FOUND_KEYCLOAK="Client not found."
    CLIENT_RETRIEVAL_FAILED = "Client retrieval failed"
    CLIENT_CREATION_FAILED = "Client creation/reactivation failed"
    ERROR_PREPARING_CLIENT_PAYLOAD = "Failed to prepare client payload"
    ERROR_FETCHING_DB_CLIENT = "Failed to fetch client from database"
    THREAD_WORKER_EXCEPTION="Thread worker failed during import"
    ERROR_IMPORTING_RESOURCES="Failed to import resources to client"
    ERROR_PROCESSING_SINGLE_CLIENT="Failed to process client"
    RESOURCE_NAME_MISSING="Resource name missing"
    RESOURCE_POST_FAILED="Failed to post resource item"
    LIST_ROLES_FAILED="Failed to list roles."
    ROLE_PROCESSING_FAILED="Failed to process roles for client"
    DB_INSERT_FAILED="Failed to insert data into the database.Please try again or contact support if the problem continues."
    KEYCLOAK_POLICY_CREATE_FAILED="Failed to create policy."
    KEYCLOAK_POLICY_DELETE_FAILED="Failed to delete policy."
    KEYCLOAK_ROLE_DELETE_FAILED="Failed to delete role."
    KEYCLOAK_CLIENT_DELETION_FAILED = "Keycloak client deletion failed"
    CLIENT_SCOPE_DELETE_FAILED="Failed to delete client scopes"
    CLIENT_DELETION_FAILED = "Client deletion process failed"
    CLIENT_SCOPES_DELETION_FAILED = "Failed to delete client-specific scopes"
    ROLE_LIST_FAILED = "Failed to list roles for the given client"
    ROLE_CREATION_FAILED = "Failed to create roles for one or more clients"
    ROLE_DEACTIVATION_FAILED = "Failed to deactivate roles for deleted client"
    ROLE_DELETE_FAILED = "Failed to delete roles for clients"
    CREATE_ROLES_FAILED="Failed to create roles."
    DELETE_ROLES_FAILED="Failed to delete roles."
    DEACTIVATE_ROLES_FAILED="Failed to deactivate roles in db."
    INVALID_INPUT="Invalid input provided"
    DB_SAVE_ERROR="Failed to save role details to database"
    DB_UPDATE_ERROR="Failed to deactivate roles for the client"
    DB_REACTIVATE_ERROR="Failed to reactivate role"
    ROLE_NOT_FOUND="Role id  not found while logging action."
    UNEXPECTED_ERROR="Unexpected error occurred while logging role action."
# Instance to use in code
err_constants = ErrorException()


# ==========================
# Custom Exception Class
# ==========================
class CustomException(Exception):
    def __init__(self, status_code: int, message: str, details: str = ""):
        self.status_code = status_code
        self.message = message
        self.details = details

    def __str__(self):
        return f"CustomException(status_code={self.status_code}, message={self.message}, details={self.details})"

    def to_response(self):
        return JSONResponse(
            status_code=self.status_code,
            content={
                "status": self.status_code,
                "message": self.message,
                "details": self.details,
            },
        )
