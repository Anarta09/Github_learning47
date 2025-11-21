import logging
from datetime import datetime
from sqlalchemy.orm import Session
from database.models.client_logs_model import ClientLogs
from database.models.client_model import Client

log = logging.getLogger(__name__)

def log_client_scope_action(
    db: Session,
    client_identifier: str = None,
    action: str = None,
    performed_by: str = "system",
    is_active: bool = True,
    error_logs: str = None,
):
    """Logs client actions without storing extra details."""
    try:
        client_id = None
        client_uuid = None

        if client_identifier:
            client_record = db.query(Client).filter(
                (Client.display_client_id == client_identifier) | 
                (Client.client_name == client_identifier)
            ).first()
            if client_record:
                client_id = client_record.id
                client_uuid = client_record.client_uuid
            else:
                log.warning(f"Client '{client_identifier}' not found in DB. Logging without client_id.")

        log_entry = ClientLogs(
            client_id=client_id,
            client_uuid=client_uuid,
            action=action or "UNKNOWN_ACTION",
            performed_at=datetime.utcnow(),
            performed_by=performed_by or "system",
            is_active=is_active if isinstance(is_active, bool) else True,
            error_logs=error_logs
        )

        db.add(log_entry)
        db.commit()
        log.info(f"Logged client action: {action} for client_id: {client_id}")

    except Exception as e:
        db.rollback()
        log.error(f"Failed to log client action: {str(e)}")
        raise RuntimeError(f"Error logging client action: {str(e)}")
