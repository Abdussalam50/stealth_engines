from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..database.models import Client
from urllib.parse import urlparse
import re


def validate_client_access(api_key: str, referer_header: str, db: Session):
    # 1. Validasi Keberadaan API Key
    if not api_key:
        raise HTTPException(status_code=401, detail="API key is required")

    # 2. Cari Client Berdasarkan API Key (Sumber Kebenaran Utama)
    client = db.query(Client).filter(Client.api_key == api_key).first()
    
    if not client:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # 3. Validasi Status Akun
    if client.status != "active":
        raise HTTPException(status_code=403, detail="License expired or inactive")

    # 4. Validasi Hostname dari Referer (Cross-Check)
    if not referer_header:
        raise HTTPException(status_code=401, detail="Direct access not allowed")

    try:
        # Menggunakan urlparse jauh lebih aman daripada split manual
        parsed_uri = urlparse(referer_header)
        hostname = parsed_uri.hostname # Otomatis menangani port, slashes, dll.
        
        if not hostname:
            raise ValueError("Could not parse hostname")
            
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid referer format")

    # 5. Mencocokkan Hostname dengan Database
    # Izinkan localhost/127.0.0.1 untuk kebutuhan development Anda
    dev_hosts = ["localhost", "127.0.0.1"]
    
    if hostname not in dev_hosts and hostname != client.domain_name:
        raise HTTPException(
            status_code=403, 
            detail=f"Domain mismatch. Key registered for: {client.domain_name}"
        )

    return client