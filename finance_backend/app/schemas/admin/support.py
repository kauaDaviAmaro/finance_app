from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class SupportMessageAdminOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    email: EmailStr
    category: str
    subject: str
    message: str
    status: str
    admin_response: Optional[str] = None
    responded_at: Optional[datetime] = None
    responded_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupportMessageAdminCreate(BaseModel):
    user_id: Optional[int] = None
    email: EmailStr
    category: str = Field(..., pattern="^(general|technical|billing|feature)$")
    subject: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)


class SupportMessageAdminUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(pending|in_progress|resolved|closed)$")
    admin_response: Optional[str] = None
    responded_by: Optional[int] = None

