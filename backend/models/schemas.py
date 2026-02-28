"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ── Research ──────────────────────────────────
class ResearchStartRequest(BaseModel):
    niche: str = Field(..., min_length=1, max_length=200)


class ResearchSessionOut(BaseModel):
    session_id: int
    niche: str
    status: str
    products_found: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Products ──────────────────────────────────
class ProductOut(BaseModel):
    id: int
    title: str
    platform: str
    original_url: str
    price: Optional[float]
    mrp: Optional[float]
    discount_pct: Optional[float]
    rating: Optional[float]
    review_count: Optional[int]
    image_url: Optional[str]
    niche: str
    score: Optional[float]
    commission_estimate: Optional[float]
    affiliate_type: Optional[str]
    stock_status: Optional[str]
    gemini_sell_reason: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProductListOut(BaseModel):
    items: List[ProductOut]
    total: int
    page: int
    per_page: int


# ── Published Pins ─────────────────────────────
class PinOut(BaseModel):
    id: int
    product_id: Optional[int]
    niche: Optional[str]
    title: Optional[str]
    status: str
    pin_image_cloudinary_url: Optional[str]
    scheduled_time: Optional[datetime]
    posted_at: Optional[datetime]
    affiliate_type: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class PinListOut(BaseModel):
    items: List[PinOut]
    total: int


# ── Settings ───────────────────────────────────
class SettingsIn(BaseModel):
    gemini_api_key: Optional[str] = ""
    pinterest_app_id: Optional[str] = ""
    pinterest_app_secret: Optional[str] = ""
    pinterest_access_token: Optional[str] = ""
    instagram_app_id: Optional[str] = ""
    instagram_app_secret: Optional[str] = ""
    instagram_access_token: Optional[str] = ""
    amazon_access_key: Optional[str] = ""
    amazon_secret_key: Optional[str] = ""
    amazon_associate_tag: Optional[str] = ""
    cuelinks_api_key: Optional[str] = ""
    gmail_address: Optional[str] = ""
    gmail_app_password: Optional[str] = ""
    notification_email: Optional[str] = ""


class SettingsOut(BaseModel):
    gemini_api_key: str = ""
    pinterest_app_id: str = ""
    pinterest_app_secret: str = ""
    pinterest_access_token: str = ""
    instagram_app_id: str = ""
    instagram_app_secret: str = ""
    instagram_access_token: str = ""
    amazon_access_key: str = ""
    amazon_secret_key: str = ""
    amazon_associate_tag: str = ""
    cuelinks_api_key: str = ""
    gmail_address: str = ""
    gmail_app_password: str = ""
    notification_email: str = ""


class TestConnectionOut(BaseModel):
    ok: bool
    message: str


# ── Dashboard ──────────────────────────────────
class DashboardStats(BaseModel):
    pins_today: int = 0
    total_clicks: int = 0
    commission: float = 0.0
    pending: int = 0


class ActivityItem(BaseModel):
    id: int
    message: str
    time: str


class ActivityOut(BaseModel):
    items: List[ActivityItem]


# ── Notifications ─────────────────────────────
class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    message: str
    is_read: bool
    action_url: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
