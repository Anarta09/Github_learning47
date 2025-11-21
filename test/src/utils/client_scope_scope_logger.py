import json
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from database.models.client_scope_logs_model import ClientScopeLogs  # updated model

log = logging.getLogger(__name__)

def log_client_scope_action_scope(
    db: Session,
    client_id: int,
    client_uuid: str,
    client_name: str,  # required for NOT NULL
    action: str,
    operation: str,
    performed_by: str = "system",
    client_mapping_details: dict | str = None,
    error_logs: str = None,
    is_active: bool = True
):
    """
    Logs actions for client scopes into client_scope_logs table.
    """
    try:
        # Convert dict to JSON string
        if client_mapping_details and isinstance(client_mapping_details, dict):
            client_mapping_details = json.dumps(client_mapping_details)

        # Create log entry
        log_entry = ClientScopeLogs(
            client_id=client_id,
            client_uuid=client_uuid,
            client_name=client_name,
            action=action,
            operation=operation,
            performed_by=performed_by,
            performed_at=datetime.utcnow(),
            client_mapping_details=client_mapping_details,
            error_logs=error_logs,
            is_active=is_active
        )

        db.add(log_entry)
        db.commit()
        log.info(f"[SCOPE] Logged client action: {action} ({operation}) for client: {client_name}")

    except Exception as e:
        db.rollback()
        log.error(f"[SCOPE] Failed to log client scope action: {str(e)}")
        raise RuntimeError(f"Error logging client scope action: {str(e)}")
