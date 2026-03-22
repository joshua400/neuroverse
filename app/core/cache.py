import os
import json
import time
from typing import Any, Optional
import httpx

_local_cache = {}

class CacheManager:
    """Redis / In-Memory Cache layer for Horizontal Scaling.
    
    Seamlessly utilizes HTTP REST Redis (e.g. Upstash) if
    REDIS_REST_URL and REDIS_REST_TOKEN are set in .env.
    Otherwise, defaults to an in-process local dict.
    """
    def __init__(self):
        self.redis_url = os.getenv("REDIS_REST_URL")
        self.redis_token = os.getenv("REDIS_REST_TOKEN")

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        if self.redis_url and self.redis_token:
            url = f"{self.redis_url}/set/{key}"
            if ttl_seconds:
                url += f"/EX/{ttl_seconds}"
            
            headers = {"Authorization": f"Bearer {self.redis_token}"}
            payload = value if isinstance(value, str) else json.dumps(value)
            
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(url, content=payload, headers=headers)
                    return
                except httpx.RequestError:
                    pass  # Fallback to local
        
        # Local Fallback
        expiry = time.time() + ttl_seconds if ttl_seconds else None
        _local_cache[key] = {"value": value, "expiry": expiry}

    async def get(self, key: str) -> Optional[Any]:
        if self.redis_url and self.redis_token:
            url = f"{self.redis_url}/get/{key}"
            headers = {"Authorization": f"Bearer {self.redis_token}"}
            
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(url, headers=headers)
                    result = response.json().get("result")
                    if result is not None:
                        try:
                            return json.loads(result)
                        except json.JSONDecodeError:
                            return result
                    return None
                except httpx.RequestError:
                    pass  # Fallback to local

        # Local Fallback
        record = _local_cache.get(key)
        if not record:
            return None
        if record["expiry"] and time.time() > record["expiry"]:
            del _local_cache[key]
            return None
        return record["value"]

cache_manager = CacheManager()
