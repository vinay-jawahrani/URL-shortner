import httpx
from typing import Optional

async def get_location_info(ip: str) -> dict:
    """Fetch location info from ip-api.com"""
    if ip.startswith("127.") or ip.startswith("192.168.") or ip == "::1":
        return {"city": "Local", "country": "Local"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://ip-api.com/json/{ip}?fields=city,country", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "city": data.get("city"),
                        "country": data.get("country")
                    }
    except Exception:
        pass
    return {"city": None, "country": None}