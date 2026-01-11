from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DBSession
from datetime import datetime

from .database.config import get_db
from .database.models import Session, Admin

def get_current_admin(request: Request, db: DBSession = Depends(get_db)):
    """Validate session token and return admin username"""
    session_token = request.cookies.get("session")
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Query session from database
    session = db.query(Session).filter(Session.token == session_token).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    
    # Check if session expired
    if session.expires_at < datetime.utcnow():
        db.delete(session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
    
    # Get admin user
    admin = db.query(Admin).filter(Admin.id == session.user_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return admin.username

def get_current_admin_with_redirect(request: Request, db: DBSession = Depends(get_db)):
    """Validate session for page routes that need redirect on failure"""
    session_token = request.cookies.get("session")
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    
    # Query session from database
    session = db.query(Session).filter(Session.token == session_token).first()
    if not session or session.expires_at < datetime.utcnow():
        if session:
            db.delete(session)
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    
    # Get admin user
    admin = db.query(Admin).filter(Admin.id == session.user_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    
    return admin.username
