import asyncio
import sys
import uuid
import base64
import secrets
from datetime import datetime, timedelta

# --- 1. WINDOWS ASYNCIO FIX (Wajib Paling Atas) ---
# if sys.platform == 'win32':
    # ProactorEventLoop diperlukan oleh Playwright untuk subprocess di Windows
    # asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request, Form, Response, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import httpx

# Import internal aplikasi
from .database.models import AuditLog, Client, Admin, Session as DBSession
from .database.config import get_db,engine,Base
from .core.engine import generate_stealth
from .hasher import verify_pass
from .services.payment import router as payment_router
from .routers import pseo
from .routers import admin_domains
from .dependencies import get_current_admin_with_redirect, get_current_admin
from .middleware import DynamicCORSMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware
from .utils.sanitizer import sanitize_text, sanitize_html

app = FastAPI(title="Stealth Engine API")

# --- 2. MIDDLEWARE CONFIGURATION ---
# Custom security middleware
app.add_middleware(RateLimitMiddleware) # Rate limiting should usually be early in the stack
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(DynamicCORSMiddleware)

templates = Jinja2Templates(directory="app/templates")

# --- 3. STARTUP CHECK ---
@app.on_event("startup")
async def startup_event():
    """Memastikan loop yang berjalan mendukung Playwright"""
    loop = asyncio.get_running_loop()
    print(f"INFO: Application started with loop: {type(loop).__name__}")

# --- 4. CORE ENDPOINTS (AUDITOR & ENGINE) ---
Base.metadata.create_all(bind=engine)
@app.get("/", response_class=FileResponse)
async def serve_index():
    # Serve index.html from root with security headers
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_path, "index.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTMLResponse(content="<h1>index.html not found</h1>", status_code=404)

class AuditRequest(BaseModel):
    payload: str

@app.post("/x92j-scan")
async def secure_audit(data: AuditRequest, db: Session = Depends(get_db)):
    target_url = "Unknown"
    try:
        # Decode payload (salt 5 di depan, 4 di belakang)
        pure_base64 = data.payload[5:-4] 
        target_url = base64.b64decode(pure_base64).decode('utf-8')
        
        # Sanitize target URL to prevent log injection or XSS in admin panel
        sanitized_url = sanitize_text(target_url)

        # check Auditor Service (Remote HF or Local)
        service_url = os.getenv("https://cadels-anti-scraping.hf.space/audit")
        if service_url:
            print(f"DEBUG: Redirecting audit to remote service: {service_url}")
            async with httpx.AsyncClient() as client:
                try:
                    hf_res = await client.post(
                        f"{service_url.rstrip('/')}/audit",
                        json={"url": target_url},
                        timeout=60.0
                    )
                    result = hf_res.json()
                except Exception as hf_e:
                    print(f"DEBUG: Remote Auditor Error: {str(hf_e)}")
                    result = {"is_protected": False, "score": 0, "details": "Remote Service Offline", "tech_stack": {}}
        else:
            print(f"DEBUG: Starting local Playwright audit for {sanitized_url}")
            from .core.auditor import run_stealth_audit
            result = await run_stealth_audit(target_url)
        
        # Simpan Log
        new_log = AuditLog(
            id=str(uuid.uuid4()),
            target_url=sanitized_url,
            status_result="Protected" if result.get("is_protected") else "Vulnerable",
            details=sanitize_text(result.get("details", "Audit Success"))
        )
        db.add(new_log)
        db.commit()

        return result 

    except Exception as e:
        return {
            "is_protected": False,
            "score": 0,
            "details": f"Error: {str(e)}",
            "tech_stack": {"waf": "Error", "poisoning_level": "None"}
        }

@app.get("/loader.js")
async def stealth_engine(request: Request, domain: str = Query(None), db: Session = Depends(get_db)):
    referer=request.headers.get("referer")
 
    if not referer:
        return Response(content="console.error('Stealth: Invalid request');", media_type="application/javascript")
    if not domain:
        return Response(content="console.error('Stealth: Domain missing');", media_type="application/javascript")

    client = db.query(Client).filter(Client.domain_name == domain).first()
    
    # Auto-register jika domain belum terdaftar (Free Trial)
    if not client:
        # Sanitize domain name
        s_domain = sanitize_text(domain)
        client = Client(
            id=str(uuid.uuid4()),
            client_name=f"Trial_{s_domain}",
            domain_name=s_domain,
            api_key=str(uuid.uuid4()),
            plan="free",
            status="active"
        )
        db.add(client)
        db.commit()
        db.refresh(client)

    now = datetime.utcnow()

    # Logika Expiry Paket
    if client.plan == "free":
        if now > (client.created_at + timedelta(days=1)):
            return Response(content="console.warn('Stealth: Free Trial Expired. Upgrade to Tactical.');", media_type="application/javascript")
    elif client.plan == "tactical":
        if now > (client.updated_at + timedelta(days=30)):
            return Response(content="console.warn('Stealth: Monthly Subscription Expired.');", media_type="application/javascript")

    if client.status == "active":
        js_code = generate_stealth(client.domain_name, mode=client.plan)
        return Response(content=js_code, media_type="application/javascript")
    
    return Response(content="console.error('Stealth: Protection Revoked');", media_type="application/javascript")

# --- 5. UI / PAGES ENDPOINTS ---

@app.get("/index", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_process(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin and verify_pass(password, admin.password):
        # Generate secure session token
        session_token = secrets.token_urlsafe(32)
        session_expires = datetime.utcnow() + timedelta(days=1)  # 24 hours
        
        # Get client IP and user agent
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Create session record
        new_session = DBSession(
            id=str(uuid.uuid4()),
            user_id=admin.id,
            token=session_token,
            expires_at=session_expires,
            ip_address=client_ip,
            user_agent=user_agent
        )
        db.add(new_session)
        db.commit()
        
        # Set secure cookie
        res = RedirectResponse(url="/admin", status_code=303)
        res.set_cookie(
            key="session",
            value=session_token,
            httponly=True,  # JavaScript cannot access
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",  # CSRF protection
            max_age=86400  # 24 hours in seconds
        )
        return res
    return RedirectResponse(url="/login?error=1", status_code=303)

@app.get("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    # Invalidate session in database
    session_token = request.cookies.get("session")
    if session_token:
        db.query(DBSession).filter(DBSession.token == session_token).delete()
        db.commit()
    
    res = RedirectResponse(url="/login", status_code=303)
    res.delete_cookie("session")
    return res

# --- 6. ADMIN PANEL ENDPOINTS ---

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db), admin: str = Depends(get_current_admin_with_redirect)):
    clients = db.query(Client).all()
    return templates.TemplateResponse("admin.html", {"request": request, "clients": clients})

@app.get("/admin/logs", response_class=HTMLResponse)
async def view_logs(request: Request, db: Session = Depends(get_db), admin: str = Depends(get_current_admin_with_redirect)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()
    return templates.TemplateResponse("logs.html", {"request": request, "audit_logs": logs})

@app.get("/admin/toggle-status/{client_id}")
async def toggle_client_status(client_id: str, db: Session = Depends(get_db), admin: str = Depends(get_current_admin_with_redirect)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if client:
        client.status = 'active' if client.status == "revoked" else "revoked"
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/admin/delete-log/{log_id}")
async def delete_log(log_id: str, db: Session = Depends(get_db), admin: str = Depends(get_current_admin_with_redirect)):
    log_entry = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if log_entry:
        db.delete(log_entry)
        db.commit()
    return RedirectResponse(url="/admin/logs", status_code=303)

@app.get("/admin/clear-all-logs")
async def clear_all_logs(db: Session = Depends(get_db), admin: str = Depends(get_current_admin_with_redirect)):
    db.query(AuditLog).delete()
    db.commit()
    return RedirectResponse(url="/admin/logs", status_code=303)

@app.post("/admin/add-client")
async def add_client(
    name: str = Form(...),
    domain: str = Form(...),
    plan: str = Form(...),
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    # Sanitize inputs
    s_name = sanitize_text(name)
    s_domain = sanitize_text(domain)
    
    # Check duplicate
    existing = db.query(Client).filter(Client.domain_name == s_domain).first()
    if existing:
        return RedirectResponse(url="/admin?error=exists", status_code=303)
        
    new_client = Client(
        id=str(uuid.uuid4()),
        client_name=s_name,
        domain_name=s_domain,
        api_key=str(uuid.uuid4()),
        status="active",
        plan=plan
    )
    db.add(new_client)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

# Sertakan Router Eksternal
app.include_router(payment_router)
app.include_router(pseo.router)
app.include_router(pseo.public_router)
app.include_router(admin_domains.router)

@app.get("/admin/pseo-manager", response_class=HTMLResponse)
async def pseo_manager_page(request: Request, admin: str = Depends(get_current_admin_with_redirect)):
    return templates.TemplateResponse("pseo_manager.html", {"request": request})