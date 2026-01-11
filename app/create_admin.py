import uuid
from sqlalchemy.orm import Session
from .database.config import SessionLocal,engine

from .database.models import Admin,Base
from passlib.context import CryptContext
from .hasher import hash_pass
from datetime import datetime, timezone
pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

Base.metadata.create_all(bind=engine)
def create_admin():
    db=SessionLocal()
    try:
        admin=db.query(Admin).filter(Admin.username=="admin").first()
        if not admin:
            new_admin=Admin(
                id=str(uuid.uuid4()),
                name="Admin",
                username="admin",
                password=hash_pass("admin*123"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(new_admin)
            db.commit()
            print("Admin created")
        else:
            print("Admin already exists")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        db.close()

if __name__=="__main__":
    create_admin()

