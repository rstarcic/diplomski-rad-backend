from app.dashboard.schemas import DashboardResponse
from app.dashboard.service import get_dashboard
from app.dependencies import get_current_user
from app.profiles.models import Profile
from database import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard_endpoint(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    return await get_dashboard(db, current_user)
