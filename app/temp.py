# Jalankan di terminal python atau buat script temporary
from app.database.config import SessionLocal
from app.database.models import TrustedDomain

db = SessionLocal()
new_domain = TrustedDomain(domain="https://2b62fc688767.ngrok-free.app", is_active=True)
db.add(new_domain)
db.commit()
db.close()