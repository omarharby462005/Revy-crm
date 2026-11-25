import logging
from dataclasses import dataclass
from typing import Optional

from langchain_core.tools import tool
from sqlalchemy.exc import SQLAlchemyError

from models.models import Maintenance, db


logger = logging.getLogger(__name__)


@dataclass
class SaveMaintenanceResult:
    success: bool
    message: Optional[str] = None


@tool
def save_maintenance_tool(
    project_name: str,
    phone_number: str,
) -> SaveMaintenanceResult:
    """Save a new maintenance record with the project name and phone number."""
    project_name = project_name.strip()
    phone_number = phone_number.strip()
    if not 1 <= len(project_name) <= 150 or not 1 <= len(phone_number) <= 20:
        return SaveMaintenanceResult(
            success=False,
            message="A valid project name and phone number are required.",
        )

    try:
        db.session.add(Maintenance(
            project_name=project_name,
            phone_number=phone_number,
        ))
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.error("[MAINTENANCE] Could not save request")
        return SaveMaintenanceResult(
            success=False,
            message="Could not save maintenance details.",
        )

    return SaveMaintenanceResult(
        success=True,
        message="Maintenance details saved successfully.",
    )
