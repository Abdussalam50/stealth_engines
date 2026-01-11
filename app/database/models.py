from sqlalchemy import Column,Integer,String,Boolean,DateTime,JSON,Text
from .config import Base
from datetime import datetime
import uuid

class Client(Base):
    __tablename__="clients"
    id=Column(String,primary_key=True,index=True)
    client_name=Column(String)
    domain_name=Column(String,unique=True,index=True)
    api_key=Column(String,unique=True,index=True)
    status=Column(String,default="expired")
    plan = Column(String, default="free")
    created_at=Column(DateTime,default=datetime.utcnow)
    updated_at=Column(DateTime)

class Admin(Base):
    __tablename__="admin"
    id=Column(String,primary_key=True,index=True)
    name=Column(String)
    username=Column(String,unique=True,index=True)
    password=Column(String)
    created_at=Column(DateTime,default=datetime.utcnow)
    updated_at=Column(DateTime)

class AuditLog(Base):
    __tablename__="audit_logs"
    id=Column(String,primary_key=True,index=True)
    target_url=Column(String)
    status_result=Column(String)
    details = Column(String)
    created_at=Column(DateTime,default=datetime.utcnow)

class PseoEngine(Base):
    __tablename__="pseo_content"
# Identitas Unik
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # URL (Netlify akan memanggil berdasarkan slug ini)
    slug = Column(String, unique=True, index=True, nullable=False) 
    
    # Variabel PSEO
    sektor = Column(String, nullable=False)   # Contoh: 'Fintech', 'Logistik'
    
    # Konten Halaman
    title_tag = Column(String)                # Judul untuk SEO
    meta_description = Column(Text)           # Deskripsi untuk SEO
    body_content = Column(Text)               # Teks utama (narasi keamanan)
    
    # Media
    image_url = Column(String)                # Link gambar
    image_alt = Column(String)                # Teks alt gambar
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PSEOContent(slug='{self.slug}', sektor='{self.sektor}')>"

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)  # Reference to Admin.id
    token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String)
    user_agent = Column(String)
    
    def __repr__(self):
        return f"<Session(user_id='{self.user_id}', expires_at='{self.expires_at}')>"

class TrustedDomain(Base):
    __tablename__ = "trusted_domains"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    domain = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<TrustedDomain(domain='{self.domain}', is_active={self.is_active})>"