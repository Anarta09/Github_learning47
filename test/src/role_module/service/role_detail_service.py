from sqlalchemy.orm import Session
from fastapi import status
from models.role_detail_model import RoleDetail
from custom_exeptions import CustomException,err_constants,Messages
import logging

logger = logging.getLogger(__name__)


class RoleDetailService:
    def __init__(self):
        pass

    def create_role_detail(
        self,
        db: Session,
        role_name: str,
        client_id: int,
        client_uuid: str = None,
        client_name: str = None,
        created_by: str = None
    ):
        """
        Insert new role details into role_details table.
        """
        try:
            role_entry = RoleDetail(
                role_name=role_name,
                client_id=client_id,  # Must be DB PK
                client_uuid=client_uuid,
                client_name=client_name,
                created_by=created_by
            )
            db.add(role_entry)
            db.commit()
            db.refresh(role_entry)
            return role_entry

        except CustomException as err:
            logger.error(f"role_detail_service.py:create_role_detail ---> {err}", exc_info=True)
            raise err

        except Exception as err:
            db.rollback()
            logger.error(f"Exception while creating role details in DB ---> {err}")
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.DB_SAVE_ERROR,
                details=err_constants.DB_SAVE_ERROR
            )

    def deactivate_roles_by_client(self, db: Session, client_id: int, performed_by="system"):
        """
        Mark all roles of a client as inactive when the client is deleted.
        """
        try:
            roles = db.query(RoleDetail).filter(
                RoleDetail.client_id == client_id,
                RoleDetail.is_active == True
            ).all()

            for role in roles:
                role.is_active = False
                role.updated_by = performed_by

            db.commit()
            return roles

        except CustomException as err:
            logger.error(f"role_detail_service.py:deactivate_roles_by_client ---> {err}", exc_info=True)
            raise err

        except Exception as err:
            db.rollback()
            logger.error(f"Exception while deactivating roles for client ---> {err}")
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.DB_UPDATE_ERROR,
                details=err_constants.DB_UPDATE_ERROR
            )

    def reactivate_role(self, db: Session, role_name: str, client_id: int, performed_by="system"):
        """
        Re-activate a previously deactivated role when re-created for a reactivated client.
        """
        try:
            role = db.query(RoleDetail).filter(
                RoleDetail.role_name == role_name,
                RoleDetail.client_id == client_id,
                RoleDetail.is_active == False
            ).first()

            if role:
                role.is_active = True
                role.updated_by = performed_by
                db.commit()
                db.refresh(role)
                return role

            return None

        except CustomException as err:
            logger.error(f"role_detail_service.py:reactivate_role ---> {err}", exc_info=True)
            raise err

        except Exception as err:
            db.rollback()
            logger.error(f"Exception while reactivating role ---> {err}")
            raise CustomException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=Messages.DB_REACTIVATE_ERROR,
                details=err_constants.DB_UPDATE_ERROR
            )
