from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.db.models import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    full_name: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserOut(UserBase):
    id: int
    role: UserRole
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class SubscriptionStatus(BaseModel):
    role: UserRole
    subscription_status: str | None
    is_pro: bool

    class Config:
        from_attributes = True


class UserPublic(BaseModel):
    email: EmailStr
    username: str
    full_name: str | None = None
    created_at: datetime | None = None
    two_factor_enabled: bool = False

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=100)
    full_name: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)

