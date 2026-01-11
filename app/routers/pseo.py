from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from ..database.config import get_db
from ..database.models import PseoEngine
from ..schemas import PseoCreate, PseoUpdate, PseoResponse
from ..dependencies import get_current_admin
from ..utils.sanitizer import sanitize_html, sanitize_text

router = APIRouter(
    prefix="/admin/pseo",
    tags=["pseo-admin"]
)

public_router = APIRouter(
    prefix="/api/pseo",
    tags=["pseo-public"]
)

# --- Admin Routes (Protected) ---

@router.post("/create", response_model=PseoResponse)
async def create_pseo_content(
    item: PseoCreate, 
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    # Check if slug exists
    if db.query(PseoEngine).filter(PseoEngine.slug == item.slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")
    
    # Sanitize HTML content
    new_content = PseoEngine(
        id=str(uuid.uuid4()),
        slug=item.slug,
        sektor=item.sektor,
        title_tag=sanitize_text(item.title_tag),
        meta_description=sanitize_text(item.meta_description),
        body_content=sanitize_html(item.body_content),
        image_url=item.image_url,
        image_alt=sanitize_text(item.image_alt)
    )
    db.add(new_content)
    db.commit()
    db.refresh(new_content)
    return new_content

@router.post("/upload")
async def upload_pseo_json(
    items: List[PseoCreate],
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    created_count = 0
    errors = []
    
    for item in items:
        if db.query(PseoEngine).filter(PseoEngine.slug == item.slug).first():
            errors.append(f"Slug '{item.slug}' skipped (duplicate)")
            continue
        
        # Sanitize HTML content
        new_content = PseoEngine(
            id=str(uuid.uuid4()),
            slug=item.slug,
            sektor=item.sektor,
            title_tag=sanitize_text(item.title_tag),
            meta_description=sanitize_text(item.meta_description),
            body_content=sanitize_html(item.body_content),
            image_url=item.image_url,
            image_alt=sanitize_text(item.image_alt)
        )
        db.add(new_content)
        created_count += 1
    
    db.commit()
    return {"message": f"Successfully created {created_count} items", "errors": errors}

@router.get("/list", response_model=List[PseoResponse])
async def list_pseo_content(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    return db.query(PseoEngine).order_by(PseoEngine.created_at.desc()).all()

@router.put("/{id}", response_model=PseoResponse)
async def update_pseo_content(
    id: str,
    item: PseoUpdate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    content = db.query(PseoEngine).filter(PseoEngine.id == id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Sanitize and update only provided fields
    update_data = item.dict(exclude_unset=True)
    if "title_tag" in update_data:
        content.title_tag = sanitize_text(update_data["title_tag"])
    if "meta_description" in update_data:
        content.meta_description = sanitize_text(update_data["meta_description"])
    if "body_content" in update_data:
        content.body_content = sanitize_html(update_data["body_content"])
    if "image_alt" in update_data:
        content.image_alt = sanitize_text(update_data["image_alt"])
    # Other non-HTML fields can be updated directly
    for key in ["slug", "sektor", "image_url"]:
        if key in update_data:
            setattr(content, key, update_data[key])
    
    db.commit()
    db.refresh(content)
    return content

@router.delete("/{id}")
async def delete_pseo_content(
    id: str,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    content = db.query(PseoEngine).filter(PseoEngine.id == id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    db.delete(content)
    db.commit()
    return {"message": "Content deleted"}

@router.delete("/clear-all")
async def clear_all_pseo_content(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    db.query(PseoEngine).delete()
    db.commit()
    return {"message": "All PSEO content cleared"}

from fastapi.responses import HTMLResponse, FileResponse
import os

# --- Public API Routes ---

@public_router.get("/view", response_class=FileResponse)
async def view_pseo_page():
    # Helper to find the file in looking up from current directory
    # expected: c:/xampp/htdocs/stealth-scrapper/pseo.html
    # current: .../stealth_engine/app/routers/pseo.py
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    file_path = os.path.join(base_path, "pseo.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTMLResponse(content="<h1>pseo.html not found</h1>", status_code=404)

@public_router.get("/list", response_model=List[PseoResponse])
async def get_public_pseo_list(db: Session = Depends(get_db)):
    """Public endpoint to list all PSEO content for the sidebar"""
    return db.query(PseoEngine).order_by(PseoEngine.created_at.desc()).all()

@public_router.get("/{slug}", response_model=PseoResponse)
async def get_pseo_content(slug: str, db: Session = Depends(get_db)):
    content = db.query(PseoEngine).filter(PseoEngine.slug == slug).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content
