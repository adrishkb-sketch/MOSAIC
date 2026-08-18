from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import UserActivity
from app.db.schemas import ActivityResponse
from typing import List

router = APIRouter()

@router.get("/logs", response_model=List[ActivityResponse])
def list_activities(
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db)
):
    try:
        return db.query(UserActivity).filter(
            UserActivity.user_id == email
        ).order_by(UserActivity.timestamp.desc()).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/{task_id}", response_model=ActivityResponse)
def get_activity_details(
    task_id: str,
    db: Session = Depends(get_db)
):
    activity = db.query(UserActivity).filter(UserActivity.task_id == task_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Audit log for task not found")
    return activity
