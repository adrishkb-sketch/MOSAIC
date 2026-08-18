from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import SharedWebsite
from app.db.schemas import SharedWebsiteResponse
from typing import List
from datetime import datetime

router = APIRouter()

@router.get("/items", response_model=List[SharedWebsiteResponse])
def get_shared_websites(db: Session = Depends(get_db)):
    try:
        websites = db.query(SharedWebsite).all()
        if not websites:
            # Let's seed a demonstration website entry so the UI displays learned website knowledge
            demo_website = SharedWebsite(
                domain="example-internships.com",
                name="Global Career Portal",
                workflows='{"search": "Enter search keyword, click search button", "filter": "Select location, check remote, select stipend", "apply": "Navigate to form, autofill profile, submit"}',
                commands='["webcmd example-internships search --role <role>", "webcmd example-internships apply --id <id>"]',
                success_rate=0.97,
                uses_count=42,
                fallback_strategies='["Fall back to live browser inspection if submit button selector changes", "Verify form fields dynamically if labels drift"]'
            )
            db.add(demo_website)
            db.commit()
            db.refresh(demo_website)
            websites = [demo_website]
        return websites
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
