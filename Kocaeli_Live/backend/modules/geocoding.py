import aiohttp
from core.database import db
from core.config import OPENCAGE_API_KEY

async def get_coordinates(location_name):
    """
    Looks up coordinates for a given Kocaeli district using the OpenCage Geocoding API.
    Uses MongoDB caching to avoid redundant API calls and save limit quota.
    """
    if location_name == "Kocaeli (Merkez)":
        query = "İzmit, Kocaeli, Turkey"
    else:
        query = f"{location_name}, Kocaeli, Turkey"
        
    cache_col = db["geocode_cache"]
    
    # 1. Check MongoDB Cache first to save quota!
    cached = await cache_col.find_one({"query": query})
    if cached:
        return cached["lat"], cached["lng"]
        
    # 2. Call OpenCage API if not cached
    if not OPENCAGE_API_KEY:
        print("Missing OpenCage API Key")
        return 40.7654, 29.9408 # Generic Kocaeli Izmit fallback
        
    url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        "q": query,
        "key": OPENCAGE_API_KEY,
        "limit": 1,
        "no_annotations": 1
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("results"):
                        lat = data["results"][0]["geometry"]["lat"]
                        lng = data["results"][0]["geometry"]["lng"]
                        
                        # 3. Save to MongoDB Cache instantly
                        await cache_col.insert_one({"query": query, "lat": lat, "lng": lng})
                        return lat, lng
    except Exception as e:
        print(f"Geocoding error: {e}")
        
    # Final Fallback
    return 40.7654, 29.9408
