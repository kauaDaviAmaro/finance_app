from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.db.models import UserRole


class UserAdminOut(BaseModel):
    """Schema de saída para usuário no admin - SEM hashed_password"""
    id: int
    email: EmailStr
    username: str
    is_active: bool
    is_verified: bool
    role: UserRole
    stripe_customer_id: Optional[str] = None
    subscription_status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserAdminCreate(BaseModel):
    """Schema para criar usuário no admin - com password plain text"""
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=128)
    is_active: bool = True
    is_verified: bool = False
    role: UserRole = UserRole.USER
    stripe_customer_id: Optional[str] = None
    subscription_status: Optional[str] = None


class UserAdminUpdate(BaseModel):
    """Schema para atualizar usuário no admin - password opcional"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=100)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[UserRole] = None
    stripe_customer_id: Optional[str] = None
    subscription_status: Optional[str] = None

