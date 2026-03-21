import re
import json
import math
import asyncio
import aiohttp
import traceback

OLLAMA_URL = "http://localhost:11434"
OLLAMA_CHAT_MODEL = "llama3" 
OLLAMA_EMBED_MODEL = "nomic-embed-text"

# Fallbacks just in case the LLM is perfectly unavailable so it doesn't crash the test visually
CATEGORIES = {
    "Traffic": ["kaza", "trafik", "çarpış", "devril", "yaralan", "araç"],
    "Fire": ["yangın", "itfaiye", "alev", "kundaklama", "yandı", "duman"],
    "Electricity": ["elektrik", "kesinti", "sedaş", "karanlık", "arıza", "trafo"],
    "Theft": ["hırsız", "çal", "gözaltı", "soygun", "polis", "yakalan", "gasp"],
    "Culture": ["etkinlik", "konser", "festival", "fuar", "sergi", "tiyatro", "gösteri"]
}

DISTRICTS = [
    "İzmit", "Gebze", "Gölcük", "Karamürsel", 
    "Körfez", "Derince", "Kartepe", "Başiskele", 
    "Çayırova", "Darıca", "Dilovası", "Kandıra"
]

def fallback_classify(text, title=""):
    combined = (title + " " + text).lower()
    scores = {cat: 0 for cat in CATEGORIES}
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in combined: scores[cat] += 1
    best_cat = max(scores, key=scores.get)
    return best_cat if scores[best_cat] > 0 else "Culture"

def fallback_location(text, title=""):
    combined = (title + " " + text).lower()
    for d in DISTRICTS:
        if d.lower() in combined.replace('i̇', 'i').replace('ı', 'I'):
            return d
    return "Kocaeli (Merkez)"

# ---------- LLM INTEGRATION ----------- #

async def fetch_llm_classification(session, title, text):
    prompt = f"""
You are an expert Turkish news analyst. Analyze the following news snippet and respond strictly in JSON.
Categories MUST be EXACTLY ONE of: "Traffic", "Fire", "Electricity", "Theft", "Culture".
Location MUST be the exact Kocaeli district mentioned (e.g., "İzmit", "Gebze"), or "Kocaeli (Merkez)" if not specified.

Title: {title}
Content: {text[:800]}

Format: {{"category": "...", "location": "..."}}
"""
    try:
        async with session.post(f"{OLLAMA_URL}/api/generate", json={
            "model": OLLAMA_CHAT_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=8) as resp:
            data = await resp.json()
            res = json.loads(data.get("response", "{}"))
            return res.get("category"), res.get("location")
    except Exception:
        return None, None

async def fetch_llm_embedding(session, text):
    try:
        async with session.post(f"{OLLAMA_URL}/api/embeddings", json={
            "model": OLLAMA_EMBED_MODEL,
            "prompt": text[:1000]
        }, timeout=8) as resp:
            data = await resp.json()
            return data.get("embedding", [])
    except Exception:
        return []

def compute_cosine_similarity(vec1, vec2):
    if not vec1 or not vec2: return 0.0
    dot = sum(a*b for a, b in zip(vec1, vec2))
    norma = math.sqrt(sum(a*a for a in vec1))
    normb = math.sqrt(sum(b*b for b in vec2))
    return dot / (norma * normb) if norma * normb > 0 else 0.0

async def process_single_article(session, item, accepted_embeddings):
    title = item.get("title", "")
    content = item.get("raw_content", "")
    combined = f"{title} {content}"

    # 1. Gather LLM classification and LLM embedding concurrently
    (llm_cat, llm_loc), embedding = await asyncio.gather(
        fetch_llm_classification(session, title, content),
        fetch_llm_embedding(session, combined)
    )

    # 2. Determine Category & Location (Fallback if LLM is offline/times out)
    item["category"] = llm_cat if llm_cat else fallback_classify(content, title)
    item["location"] = llm_loc if llm_loc else fallback_location(content, title)
    
    # 3. LLM Embedding Duplicate Detection (>= 90%)
    is_duplicate = False
    max_sim = 0.0
    
    if embedding:
        for emb in accepted_embeddings:
            sim = compute_cosine_similarity(embedding, emb)
            if sim > max_sim:
                max_sim = sim
                
        if max_sim >= 0.90:
            is_duplicate = True
        else:
            accepted_embeddings.append(embedding)

    item["is_duplicate"] = is_duplicate
    item["similarity_score"] = float(max_sim)
    item["used_llm"] = bool(llm_cat or embedding) # For tracking in UI
    
    return item

async def process_nlp_for_articles(articles):
    if not articles: return []
    processed = []
    accepted_embeddings = [] # Stores successfully parsed embeddings
    
    async with aiohttp.ClientSession() as session:
        # Process sequentially to prevent duplicate race conditions
        for item in articles:
            try:
                processed_item = await process_single_article(session, item, accepted_embeddings)
                processed.append(processed_item)
            except Exception as e:
                print(f"Failed to process article: {e}")
                traceback.print_exc()

    return processed
