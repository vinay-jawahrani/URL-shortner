from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import random
import string
from collections import defaultdict
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, get_db, Base
from app import models, schemas, auth, cache, services

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener API",
    description="Shorten URLs with click analytics",
    version="1.0.0"
)

# --- Helper Functions ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def get_client_info(request: Request) -> dict:
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    device = "Desktop"
    browser = "Unknown"
    if "mobile" in user_agent.lower():
        device = "Mobile"
    elif "tablet" in user_agent.lower():
        device = "Tablet"
    if "chrome" in user_agent.lower():
        browser = "Chrome"
    elif "firefox" in user_agent.lower():
        browser = "Firefox"
    elif "safari" in user_agent.lower():
        browser = "Safari"
    elif "edge" in user_agent.lower():
        browser = "Edge"
    return {"ip": client_ip, "device": device, "browser": browser}

# --- Endpoints ---

@app.get("/")
async def root():
    return {"message": "URL Shortener API is running!", "docs": "/docs"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "redis": "connected" if cache.cache.is_connected() else "not available"
    }

# --- Authentication ---

@app.post("/api/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=auth.hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# --- URL Shortening ---

@app.post("/api/urls/shorten", response_model=schemas.URLResponse, status_code=status.HTTP_201_CREATED)
def shorten_url(
    request: schemas.URLShortenRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if custom code is provided
    short_code = request.custom_code
    if short_code:
        existing = db.query(models.URL).filter(models.URL.short_code == short_code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Custom code already taken")
    else:
        # Generate unique short code
        short_code = generate_short_code()
        while db.query(models.URL).filter(models.URL.short_code == short_code).first():
            short_code = generate_short_code()
    
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
    
    db_url = models.URL(
        original_url=request.original_url,
        short_code=short_code,
        user_id=current_user.id,
        expires_at=expires_at
    )
    
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    
    return {
        "id": db_url.id,
        "original_url": db_url.original_url,
        "short_code": db_url.short_code,
        "short_url": f"https://short.ly/{db_url.short_code}",
        "clicks": db_url.clicks,
        "created_at": db_url.created_at,
        "expires_at": db_url.expires_at
    }

@app.get("/{short_code}")
async def redirect_to_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    # Check cache first
    cache_key = f"url:{short_code}"
    cached = await cache.cache.get(cache_key)
    
    if cached:
        original_url = cached.get("original_url")
        url_id = cached.get("url_id")
    else:
        db_url = db.query(models.URL).filter(models.URL.short_code == short_code).first()
        if not db_url:
            raise HTTPException(status_code=404, detail="URL not found")
        
        # Check if expired
        if db_url.expires_at and db_url.expires_at < datetime.utcnow():
            raise HTTPException(status_code=410, detail="URL has expired")
        
        original_url = db_url.original_url
        url_id = db_url.id
        
        # Cache for 5 minutes
        await cache.cache.set(cache_key, {"original_url": original_url, "url_id": url_id}, ttl=300)
    
    # Track click
    client_info = get_client_info(request)
    location = await services.get_location_info(client_info["ip"])
    
    click = models.Click(
        url_id=url_id,
        ip=client_info["ip"],
        city=location.get("city"),
        country=location.get("country"),
        device=client_info["device"],
        browser=client_info["browser"]
    )
    
    # Update click count
    db_url = db.query(models.URL).filter(models.URL.id == url_id).first()
    if db_url:
        db_url.clicks += 1
    
    db.add(click)
    db.commit()
    
    return RedirectResponse(url=original_url, status_code=302)

#Analytics
# --- Analytics Endpoints ---

@app.get("/api/analytics/{short_code}", response_model=schemas.URLAnalyticsResponse)
def get_url_analytics(
    short_code: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for a specific short URL"""
    db_url = db.query(models.URL).filter(models.URL.short_code == short_code).first()
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    # Check if the current user owns this URL
    if db_url.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to view this URL's analytics")
    
    # Get all clicks for this URL
    clicks = db.query(models.Click).filter(models.Click.url_id == db_url.id).order_by(
        models.Click.clicked_at.desc()
    ).limit(100).all()
    
    return {
        "short_code": db_url.short_code,
        "original_url": db_url.original_url,
        "total_clicks": db_url.clicks,
        "clicks_data": [
            {
                "ip": c.ip,
                "city": c.city,
                "country": c.country,
                "device": c.device,
                "browser": c.browser,
                "clicked_at": c.clicked_at
            }
            for c in clicks
        ]
    }

@app.get("/api/analytics/summary")
def get_click_summary(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary analytics for all URLs owned by the current user"""
    # Get all URLs for the current user
    urls = db.query(models.URL).filter(models.URL.user_id == current_user.id).all()
    
    total_clicks = sum(url.clicks for url in urls)
    
    # Top 10 most clicked URLs
    top_urls = sorted(urls, key=lambda x: x.clicks, reverse=True)[:10]
    top_urls_data = [
        {
            "short_code": url.short_code,
            "original_url": url.original_url[:50] + "..." if len(url.original_url) > 50 else url.original_url,
            "clicks": url.clicks,
            "created_at": url.created_at
        }
        for url in top_urls
    ]
    
    # Clicks by day (last 7 days)
    from datetime import timedelta
    clicks_by_day = defaultdict(int)
    today = datetime.utcnow().date()
    
    for url in urls:
        clicks = db.query(models.Click).filter(
            models.Click.url_id == url.id,
            models.Click.clicked_at >= today - timedelta(days=7)
        ).all()
        for click in clicks:
            day = click.clicked_at.date()
            clicks_by_day[day.isoformat()] += 1
    
    return {
        "total_clicks": total_clicks,
        "total_urls": len(urls),
        "top_urls": top_urls_data,
        "clicks_by_day": dict(clicks_by_day)
    }

@app.get("/api/analytics/device-breakdown")
def get_device_breakdown(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get device and browser breakdown for all URLs owned by the current user"""
    urls = db.query(models.URL).filter(models.URL.user_id == current_user.id).all()
    url_ids = [url.id for url in urls]
    
    if not url_ids:
        return {"devices": {}, "browsers": {}}
    
    clicks = db.query(models.Click).filter(models.Click.url_id.in_(url_ids)).all()
    
    devices = defaultdict(int)
    browsers = defaultdict(int)
    cities = defaultdict(int)
    countries = defaultdict(int)
    
    for click in clicks:
        if click.device:
            devices[click.device] += 1
        if click.browser:
            browsers[click.browser] += 1
        if click.city:
            cities[click.city] += 1
        if click.country:
            countries[click.country] += 1
    
    return {
        "devices": dict(devices),
        "browsers": dict(browsers),
        "cities": dict(cities),
        "countries": dict(countries)
    }