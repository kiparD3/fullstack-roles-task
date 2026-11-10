from fastapi import APIRouter, Depends

from app.api.deps import require_permission
from app.core.authorization import Permission
from app.models import MetricsPublic

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "/",
    response_model=MetricsPublic,
    dependencies=[Depends(require_permission(Permission.METRICS_READ))],
)
def read_metrics() -> MetricsPublic:
    return MetricsPublic()
