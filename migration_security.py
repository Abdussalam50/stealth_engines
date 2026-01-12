"""
Security Database Migration Script
Creates Session and TrustedDomain tables for enhanced security
"""
import sys
from sqlalchemy import create_engine
from app.database.config import SQLALCHEMY_DATABASE_URL
from app.database.models import Base, Session, TrustedDomain
import uuid

def run_migration():
    print("[*] Starting Security Migration...")
    
    engine = create_engine(SQLALCHEMY_DATABASE_URL, 
    connect_args={
        "ssl_mode": "require",
        "server_settings":{
            "search_path":"public"
        },
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "check_same_thread": False})
    
    try:
        # Create new tables
        print("Creating Session table...")
        Session.__table__.create(engine, checkfirst=True)
        
        print("Creating TrustedDomain table...")
        TrustedDomain.__table__.create(engine, checkfirst=True)
        
        # Add default trusted domains for development
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        default_domains = [
            "http://localhost",
            "http://127.0.0.1",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
        
        print("Adding default trusted domains...")
        for domain in default_domains:
            existing = db.query(TrustedDomain).filter(TrustedDomain.domain == domain).first()
            if not existing:
                new_domain = TrustedDomain(
                    id=str(uuid.uuid4()),
                    domain=domain,
                    is_active=True
                )
                db.add(new_domain)
                print(f"  [+] Added: {domain}")
        
        db.commit()
        db.close()
        
        print("\n[SUCCESS] Migration completed successfully!")
        print("\n[INFO] Next steps:")
        print("  1. Restart the server")
        print("  2. Re-login to create new session")
        print("  3. Add production domains in /admin/domains")
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
