from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.schemas import ChatRequest, ChatResponse, ActionPlanApproval
from app.services.agent import agent_orchestrator

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    try:
        res = agent_orchestrator.chat(
            db=db,
            email=request.email,
            message=request.message,
            task_id=request.task_id
        )
        return ChatResponse(
            task_id=res["task_id"],
            status=res["status"],
            response=res["response"],
            clarification_needed=res["clarification_needed"],
            action_plan_required=res["action_plan_required"],
            action_plan=res.get("action_plan"),
            browser_active=res["browser_active"],
            browser_url=res.get("browser_url"),
            screenshot=res.get("screenshot"),
            results=res.get("results") or []
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/action-plan/{task_id}/approve")
def approve_plan_endpoint(
    task_id: str,
    approval: ActionPlanApproval,
    db: Session = Depends(get_db)
):
    try:
        from app.db.models import ActionPlan
        plan = db.query(ActionPlan).filter(
            ActionPlan.task_id == task_id,
            ActionPlan.approval_status == "pending"
        ).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Pending action plan not found")
        
        plan.approval_status = "approved" if approval.approved else "rejected"
        db.commit()
        
        return {
            "status": "success",
            "message": f"Action plan {'approved' if approval.approved else 'rejected'} successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
