
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
    try:
        payload = await request.body()
        signature = request.headers.get("X-Signature")
        
        # Verify webhook signature
        digest = hmac.new(LEMON_SECRET.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, digest):
            print("ERROR: Invalid webhook signature")
            return Response(status_code=400)

        data = await request.json()
        custom_data = data.get('meta', {}).get('custom_data', {})
        domain = custom_data.get('domain')
        plan = custom_data.get('plan')
        email = data['data']['attributes']['user_email']
        event = data['meta']['event_name']
        
        print(f"DEBUG: Webhook received - Event: {event}, Domain: {domain}, Plan: {plan}, Email: {email}")

        if event in ['order_created', 'subscription_created']:
            # Ambil domain yang kita selipkan di 'custom_data'
            domain = data['meta']['custom_data']['domain']

            parsed_uri = urlparse(domain if "://" in domain else f"http://{domain}")
            clean_domain = parsed_uri.hostname.replace("www.", "") if parsed_uri.hostname else domain
            
            print(f"DEBUG: Cleaned domain: {clean_domain}")
            
            # Cari dan aktifkan di database
            client = db.query(Client).filter(Client.domain_name == clean_domain).first()
            
            if client:
                print(f"DEBUG: Updating existing client: {client.id}")
                client.plan = plan
                client.status = "active"
                client.updated_at = datetime.utcnow()
                
                try:
                    db.commit()
                    db.refresh(client)
                    print(f"SUCCESS: DOMAIN {domain} ACTIVATED VIA LEMON SQUEEZY - Client ID: {client.id}")
                except Exception as db_error:
                    db.rollback()
                    print(f"ERROR: Failed to update client in database: {str(db_error)}")
                    raise
            else:
                print(f"DEBUG: Creating new client for domain: {clean_domain}")
                new_client = Client(
                    id=str(uuid.uuid4())[:13],
                    client_name=email,
                    domain_name=clean_domain,
                    api_key=str(uuid.uuid4())[:13],
                    status="active",
                    plan=plan
                )
                db.add(new_client)
                
                try:
                    db.commit()
                    db.refresh(new_client)
                    print(f"SUCCESS: NEW DOMAIN {domain} ADDED VIA LEMON SQUEEZY - Client ID: {new_client.id}")
                except Exception as db_error:
                    db.rollback()
                    print(f"ERROR: Failed to save new client to database: {str(db_error)}")
                    raise
                    
        return {"status": "success"}
        
    except Exception as e:
        print(f"ERROR: Webhook processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}