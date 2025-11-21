from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from fastapi import status

from models.role_log_model import RoleLog
from models.role_detail_model import RoleDetail
from models.client_model import Client

from custom_exeptions import CustomException,err_constants,Messages
import logging
logger = logging.getLogger(__name__)



class RoleLogService:
    def __init__(self):
        """Initialize RoleLogService. Currently, no setup is required."""
        pass

    # ----------------------------------------------------------------------
    def log_action(
        self,
        db: Session,
        role_id: int,
        client_id: int,
        action: str,
        error_logs: str = None,
        is_active: bool = True,
        performed_by: str = "system"
    ):
        """
        Insert an action log for a role.
        Ensures the role_id and client_id exist before logging.
        """
        try:
            # Validate role exists
            role_entry = db.query(RoleDetail).filter(RoleDetail.id == role_id).first()
            if not role_entry:
                raise CustomException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=Messages.ROLE_NOT_FOUND,
                    details=err_constants.ROLE_NOT_FOUND
                )

            # Validate client exists
            client_entry = db.query(Client).filter(Client.id == client_id).first()
            if not client_entry:
                raise CustomException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=Messages.CLIENTS_NO_MATCH,
                    details=err_constants.CLIENT_NOT_FOUND
                )

            # Create a log entry
            log_entry = RoleLog(
                role_id=role_id,
                client_id=client_id,
                action=action,
                error_logs=error_logs,
                performed_by=performed_by,
                is_active=is_active,
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return log_entry

        except CustomException as err:
            logger.error(f"role_log_service.py:log_action ---> {err}", exc_info=True)
            raise err

        except IntegrityError as err:
            db.rollback()
            logger.error(f"Exception while saving role log to DB ---> {err}")
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.DB_SAVE_ERROR,
                details=err_constants.DB_SAVE_ERROR
            )

        except Exception as err:
            db.rollback()
            logger.error(f"Exception while logging role action ---> {err}")
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.UNEXPECTED_ERROR,
                details=err_constants.UNEXPECTED_ERROR
            )

    # ----------------------------------------------------------------------
    def deactivate_logs(
        self,
        db: Session,
        role_id: int,
        client_id: int,
        updated_by: str = "system"
    ):
        """
        Soft-deactivate all logs for a given role and client.
        Sets is_active = False for all matching RoleLog entries.
        """
        try:
            logs = (
                db.query(RoleLog)
                .filter(
                    RoleLog.role_id == role_id,
                    RoleLog.client_id == client_id,
                    RoleLog.is_active == True,
                )
                .all()
            )

            if not logs:
                return {"message": f"No active logs found for role_id={role_id}, client_id={client_id}"}

            for log in logs:
                log.is_active = False
                log.updated_at = datetime.now(timezone.utc)
                log.updated_by = updated_by

            db.commit()
            return {"message": f"{len(logs)} logs deactivated for role_id={role_id}, client_id={client_id}"}

        except CustomException as err:
            logger.error(f"role_log_service.py:deactivate_logs ---> {err}", exc_info=True)
            raise err

        except Exception as err:
            db.rollback()
            logger.error(f"Exception while deactivating logs ---> {err}")
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.DB_UPDATE_ERROR,
                details=err_constants.DB_UPDATE_ERROR
            )
