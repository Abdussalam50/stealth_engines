from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PseoBase(BaseModel):
    slug: str
    sektor: str
    title_tag: Optional[str] = None
    meta_description: Optional[str] = None
    body_content: Optional[str] = None
    image_url: Optional[str] = None
    image_alt: Optional[str] = None

class PseoCreate(PseoBase):
    pass

class PseoUpdate(BaseModel):
    slug: Optional[str] = None
    sektor: Optional[str] = None
    title_tag: Optional[str] = None
    meta_description: Optional[str] = None
    body_content: Optional[str] = None
    image_url: Optional[str] = None
    image_alt: Optional[str] = None

class PseoResponse(PseoBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
