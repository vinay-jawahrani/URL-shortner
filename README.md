# URL Shortener with Analytics

[![GitHub](https://img.shields.io/badge/GitHub-Repo-black)](https://github.com/vinay-jawahrani/URL-shortner)

A full-featured URL shortener API with click analytics, JWT authentication, and Redis caching built with FastAPI and PostgreSQL.

## 🚀 Features

- **Shorten URLs** – Generate unique short codes for long URLs
- **Custom Short Codes** – Create memorable short URLs (e.g., `/google`)
- **Click Tracking** – Track IP, device, browser, and geolocation for each click
- **User Authentication** – JWT-based registration and login
- **Analytics** – Per-URL click analytics with summary dashboard
- **Redis Caching** – Cache frequently accessed URLs for faster redirects
- **Auto-generated Docs** – Swagger UI at `/docs`

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (Supabase)
- **Caching**: Redis (Upstash)
- **Authentication**: JWT + bcrypt
- **Geolocation**: ip-api.com

## 📌 API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register a new user | ❌ |
| POST | `/api/auth/login` | Login and get JWT token | ❌ |
| POST | `/api/urls/shorten` | Shorten a URL | ✅ |
| GET | `/{short_code}` | Redirect to original URL | ❌ |
| GET | `/api/analytics/{short_code}` | Get analytics for a URL | ✅ |
| GET | `/api/analytics/summary` | Get summary analytics | ✅ |
| GET | `/health` | Health check | ❌ |

## 📦 Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL
- Git

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vinay-jawahrani/URL-shortner.git
   cd URL-shortner
Create and activate virtual environment:

bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
Install dependencies:

bash
pip install -r requirements.txt
Create .env file:

env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/url_shortener_db
SECRET_KEY=your-super-secret-key
REDIS_URL=rediss://default:your_token@your_endpoint.upstash.io:6379
Create the database:

sql
CREATE DATABASE url_shortener_db;
Run the server:

bash
uvicorn app.main:app --reload
Access the API:

API: http://127.0.0.1:8000

Swagger Docs: http://127.0.0.1:8000/docs

🧪 API Testing
Register a User
bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"mypassword"}'
Login
bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=mypassword"
Shorten a URL (Requires Token)
bash
curl -X POST http://127.0.0.1:8000/api/urls/shorten \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://www.google.com","custom_code":"google"}'
Redirect (in Browser)
text
http://127.0.0.1:8000/google
Get Analytics (Requires Token)
bash
curl -X GET http://127.0.0.1:8000/api/analytics/google \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
📁 Project Structure
text
URL-shortner/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── database.py      # Database connection
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── auth.py          # JWT + bcrypt logic
│   ├── services.py      # Geolocation helper
│   └── cache.py         # Redis caching
├── venv/                # Virtual environment (ignored)
├── .env                 # Environment variables (ignored)
├── requirements.txt     # Dependencies
├── README.md            # Project documentation
└── .gitignore           # Git ignore file
🔐 Environment Variables
Variable	Description	Required
DATABASE_URL	PostgreSQL connection string	✅
SECRET_KEY	JWT secret key (strong random string)	✅
REDIS_URL	Upstash Redis connection URL	❌
📄 License
MIT

👤 Author
Vinay Jawahrani

GitHub: @vinay-jawahrani

🌟 Show Your Support
If you found this project useful, give it a ⭐ on GitHub!
