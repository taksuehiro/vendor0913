from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# ユーザー関連スキーマ
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

# ベンダー関連スキーマ
class VendorBase(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[str] = None

class VendorCreate(VendorBase):
    pass

class VendorResponse(VendorBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None