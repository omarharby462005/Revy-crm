import logging

from models.models import db
from services.messaging.client_service import ClientService

logger = logging.getLogger(__name__)


def _safe(label: str, fn, default=0):
    try:
        return fn()
    except Exception:
        db.session.rollback()
        logger.exception("[DashboardService] %s failed", label)
        return default


class DashboardService:

    def get_summary_data(self) -> dict:
        return {
            "clients_count": _safe(
                "clients count",
                ClientService.get_total_clients_count
            ),
        }