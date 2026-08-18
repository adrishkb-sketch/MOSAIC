import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.schemas import MemoryResponse, MemoryCreate, MemoryUpdate
from app.services.memory import memory_service

router = APIRouter()

@router.post("/items", response_model=MemoryResponse)
def add_memory(
    item: MemoryCreate,
    email: str = Query(..., description="User email for profile scoping"),
    db: Session = Depends(get_db)
):
    try:
        return memory_service.add_memory_item(
            db=db,
            user_id=email,
            key=item.key,
            value=item.value,
            classification=item.classification,
            source=item.source
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items", response_model=List[MemoryResponse])
def list_memories(
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db)
):
    try:
        return memory_service.get_memory_items(db=db, user_id=email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items/{memory_id}", response_model=MemoryResponse)
def get_memory(
    memory_id: int,
    db: Session = Depends(get_db)
):
    item = memory_service.get_memory_by_id(db=db, memory_id=memory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return item

@router.put("/items/{memory_id}", response_model=MemoryResponse)
def update_memory(
    memory_id: int,
    item_update: MemoryUpdate,
    db: Session = Depends(get_db)
):
    item = memory_service.update_memory_item(
        db=db,
        memory_id=memory_id,
        value=item_update.value,
        classification=item_update.classification,
        source=item_update.source
    )
    if not item:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return item

@router.delete("/items/{memory_id}")
def delete_memory(
    memory_id: int,
    db: Session = Depends(get_db)
):
    success = memory_service.delete_memory_item(db=db, memory_id=memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return {"status": "success", "message": "Memory forgotten successfully"}

@router.delete("/items")
def clear_all_memories(
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db)
):
    memory_service.clear_user_memories(db=db, user_id=email)
    return {"status": "success", "message": "All memories cleared successfully"}

@router.get("/items/{memory_id}/why")
def why_used(
    memory_id: int,
    db: Session = Depends(get_db)
):
    item = memory_service.get_memory_by_id(db=db, memory_id=memory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Memory item not found")
    
    try:
        history = json.loads(item.usage_history or "[]")
    except Exception:
        history = []
        
    return {
        "key": item.key,
        "value": item.value,
        "source": item.source,
        "classification": item.classification,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "usage_history": history,
        "shared_with_others": False,
        "added_to_global_knowledge": False,
        "explanation": f"Used locally to assist with tasks matching criteria for key '{item.key}'."
    }
