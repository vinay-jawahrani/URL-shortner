import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

class Cache:
    def __init__(self):
        self.client = None
        try:
            self.client = redis.from_url(REDIS_URL, decode_responses=True)
            self.client.ping()
            print("✅ Redis connected")
        except Exception as e:
            print(f"⚠️ Redis not available: {e}")
            self.client = None
    
    def is_connected(self):
        return self.client is not None
    
    async def get(self, key: str):
        if not self.is_connected():
            return None
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except:
            return None
    
    async def set(self, key: str, value: dict, ttl: int = 300):
        if not self.is_connected():
            return
        try:
            self.client.setex(key, ttl, json.dumps(value))
        except:
            pass

cache = Cache()