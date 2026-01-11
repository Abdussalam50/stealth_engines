import sys
import os

# Menambahkan folder saat ini ke dalam jalur pencarian Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import uuid
from app.database.config import engine,SessionLocal
from app.database.models import Base, Client

def init_database():
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized")
    db=SessionLocal()
    try:
        check_client = db.query(Client).filter(Client.client_name == "Default").first()
        if not check_client:
            new_key=str(uuid.uuid4())[:13]
            new_client=Client( 
                id=new_key,
                client_name="Default",
                domain_name="127.0.0.1",
                api_key=new_key,
                status="active",
                plan="free"
            )
            db.add(new_client)
            db.commit()
            print("Default client added")
            print("="*40)
            print(f"API Key: {new_key}")
            print(f"Domain: 127.0.0.1")
            print(f"Plan: Free")
            print("="*40)
        else:
            print(f"Default client already exists, and your API key is: {check_client.api_key}")
            print("="*40)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        db.close()

if __name__=="__main__":
    init_database()