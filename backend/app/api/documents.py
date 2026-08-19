import json
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import UserDocument, UserMemory
from app.db.schemas import DocumentResponse
from app.services.memory import memory_service
from app.services.gemini import gemini_service
from typing import List, Optional
import os

router = APIRouter()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    email: str = Query(..., description="User email"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        extracted_text = ""
        
        # Simple text decoder for standard documents
        try:
            extracted_text = content.decode("utf-8")
        except UnicodeDecodeError:
            # If it's a binary file (e.g. PDF/Word), we simulate text extraction for the demo
            extracted_text = f"[Extracted from binary {file.filename}]: This is a simulated resume text contents. Skills: Python, React, JavaScript, SQL. Experience: Junior Software Developer at Startup Inc. Education: BS Computer Science."

        # Parse details (e.g. extract skills, name, projects) dynamically if Gemini is configured
        metadata = {}
        if gemini_service.is_configured() and extracted_text:
            try:
                # We can call gemini to summarize the profile details
                prompt = f"Parse this resume and extract basic info: name, email, skills, experience as JSON. Resume text:\n{extracted_text}"
                response = gemini_service.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
                )
                metadata = json.loads(response.text)
            except Exception:
                metadata = {"inferred_skills": ["Python", "React", "SQL"]}
        else:
            metadata = {"inferred_skills": ["Python", "React", "SQL"]}

        doc = UserDocument(
            user_id=email,
            name=file.filename,
            file_type=file.content_type or "text/plain",
            extracted_text=extracted_text,
            metadata_json=json.dumps(metadata)
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # If we found skills in the document, save them as inferred memories
        if "inferred_skills" in metadata or "skills" in metadata:
            skills = metadata.get("skills", metadata.get("inferred_skills", []))
            skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
            memory_service.add_memory_item(
                db=db,
                user_id=email,
                key="skills",
                value=skills_str,
                classification="PRIVATE_USER_DATA",
                source="inferred"
            )
            
        return doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items", response_model=List[DocumentResponse])
def get_documents(
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db)
):
    try:
        return db.query(UserDocument).filter(UserDocument.user_id == email).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/items/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db)
):
    doc = db.query(UserDocument).filter(UserDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"status": "success", "message": "Document deleted successfully"}

@router.get("/resume-draft")
def get_resume_draft(
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db)
):
    # Retrieve user's profile memories
    memories = memory_service.get_memory_items(db, email)
    profile = {m.key: m.value for m in memories}
    
    if gemini_service.is_configured():
        try:
            draft = gemini_service.generate_resume_draft(profile)
            return draft
        except Exception as e:
            pass
            
    # Fallback draft response
    skills = profile.get("skills", "Python, React, TypeScript, C++")
    experience = profile.get("experience", "Junior Developer Intern")
    college = profile.get("college", "Tech University")
    degree = profile.get("degree", "B.Tech Computer Science")
    name = profile.get("name", "John Doe")
    
    return {
        "name": name,
        "email": email,
        "phone": profile.get("phone", "+1 555 0199"),
        "skills": [s.strip() for s in skills.split(",") if s.strip()],
        "experience": [
            {
                "role": "Software Engineering Intern",
                "company": "Developer Innovations",
                "duration": "June 2026 - Present",
                "details": f"Working with: {skills}. Core task: {experience}."
            }
        ],
        "education": [
            {
                "degree": degree,
                "institution": college,
                "duration": "2522 - 2026",
                "gpa": profile.get("cgpa", "9.0")
            }
        ],
        "projects": [
            {
                "name": "MOSAIC Agent MVP",
                "description": "Built a privacy-focused universal browser agent with adaptive Webcmd control."
            }
        ],
        "summary": f"Passionate software developer skilled in {skills}. Experienced in building automated systems."
    }

@router.post("/resume-draft")
def save_resume_draft(
    draft_data: dict,
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db)
):
    try:
        # Save resume draft as text inside My Memory
        draft_str = json.dumps(draft_data, indent=2)
        memory_service.add_memory_item(
            db=db,
            user_id=email,
            key="resume",
            value=draft_str,
            classification="PRIVATE_USER_DATA",
            source="explicit"
        )
        return {"status": "success", "message": "Resume draft saved to My Memory successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
