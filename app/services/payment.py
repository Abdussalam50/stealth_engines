
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from ..database.config import get_db
from ..database.models import Client
from sqlalchemy.orm import Session
from datetime import datetime
from urllib.parse import urlparse
import hashlib
import hmac
import uuid
router = APIRouter(prefix="/webhook", tags=["Payments"])
LEMON_SECRET = "st3alth_secret_2026"
@router.post("/lemonsqueezy")
async def lemonsqueezy_webhook(request: Request, db: Session = Depends(get_db)):
    payload =await request.body()
    signature=request.headers.get("X-Signature")
    digest = hmac.new(LEMON_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, digest):
        return Response(status_code=400)

    data = await request.json()
    custom_data=data.get('meta',{}).get('custom_data',{})
    domain=custom_data.get('domain')
    plan=custom_data.get('plan')
    email=data['data']['attributes']['user_email']
    event = data['meta']['event_name']

    if event in ['order_created', 'subscription_created']:
        # Ambil domain yang kita selipkan di 'custom_data'
        domain = data['meta']['custom_data']['domain']

        parsed_uri=urlparse(domain if "://" in domain else f"http://{domain}")
        clean_domain=parsed_uri.hostname.replace("www.","") if parsed_uri.hostname else domain
        # Cari dan aktifkan di database
        client = db.query(Client).filter(Client.domain_name == clean_domain).first()
        if client:
            client.plan = plan
            client.status = "active"
            client.updated_at = datetime.utcnow()
            db.commit()
            print(f"--- DOMAIN {domain} ACTIVATED VIA LEMON SQUEEZY ---")
        else:
            new_client= Client(
                id=str(uuid.uuid4())[:13],
                client_name=email,
                domain_name=clean_domain,
                api_key=str(uuid.uuid4())[:13],
                status="active",
                plan=plan
            )
            db.add(new_client)
            db.commit()
            print(f"--- NEW DOMAIN {domain} ADDED VIA LEMON SQUEEZY ---")
    return {"status": "success"}