from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.db.models import NotificationType


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    keys: Dict[str, str]  # {p256dh: "...", auth: "..."}


class PushSubscriptionOut(BaseModel):
    id: int
    user_id: int
    endpoint: str
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    user_id: int
    type: NotificationType
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None


class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: list[NotificationOut]
    unread_count: int


class NotificationReadResponse(BaseModel):
    message: str = "Notificação marcada como lida"



