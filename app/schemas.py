from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class URLShortenRequest(BaseModel):
    original_url: str
    custom_code: Optional[str] = None
    expires_in_days: Optional[int] = None

class URLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    short_url: str
    clicks: int
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ClickResponse(BaseModel):
    ip: str
    city: Optional[str]
    country: Optional[str]
    device: Optional[str]
    browser: Optional[str]
    clicked_at: datetime

class URLAnalyticsResponse(BaseModel):
    short_code: str
    original_url: str
    total_clicks: int
    clicks_data: list[ClickResponse]

class ClickSummaryResponse(BaseModel):
    total_clicks: int
    top_urls: list[dict]
    clicks_by_day: dict