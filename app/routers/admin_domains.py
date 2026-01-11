from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session as DBSession
from typing import List
import uuid

from ..database.config import get_db
from ..database.models import TrustedDomain
from ..dependencies import get_current_admin_with_redirect, get_current_admin

router = APIRouter(
    prefix="/admin/domains",
    tags=["admin-domains"]
)

@router.get("", response_class=HTMLResponse)
async def list_domains_page(
    request: Request,
    db: DBSession = Depends(get_db),
    admin: str = Depends(get_current_admin_with_redirect)
):
    from ..main import templates
    domains = db.query(TrustedDomain).order_by(TrustedDomain.created_at.desc()).all()
    return templates.TemplateResponse("admin_domains.html", {
        "request": request,
        "domains": domains,
        "admin": admin
    })

@router.post("/add")
async def add_trusted_domain(
    domain: str = Form(...),
    db: DBSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    # Basic validation
    if not domain.startswith(("http://", "https://")):
         domain = f"https://{domain}"
         
    # Check duplicate
    existing = db.query(TrustedDomain).filter(TrustedDomain.domain == domain).first()
    if existing:
        return RedirectResponse(url="/admin/domains?error=exists", status_code=303)
        
    new_domain = TrustedDomain(
        id=str(uuid.uuid4()),
        domain=domain,
        is_active=True
    )
    db.add(new_domain)
    db.commit()
    return RedirectResponse(url="/admin/domains", status_code=303)

@router.get("/delete/{id}")
async def delete_trusted_domain(
    id: str,
    db: DBSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    domain = db.query(TrustedDomain).filter(TrustedDomain.id == id).first()
    if domain:
        db.delete(domain)
        db.commit()
    return RedirectResponse(url="/admin/domains", status_code=303)

@router.get("/toggle/{id}")
async def toggle_domain_status(
    id: str,
    db: DBSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    domain = db.query(TrustedDomain).filter(TrustedDomain.id == id).first()
    if domain:
        domain.is_active = not domain.is_active
        db.commit()
    return RedirectResponse(url="/admin/domains", status_code=303)
