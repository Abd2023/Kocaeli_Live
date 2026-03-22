import os
import re
import json
import logging
import asyncio
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Fallbacks just in case the SLM is unavailable
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

# ---------- OFFLINE SLM INTEGRATION ----------- #

SLM_MODEL = None

def init_slm():
    global SLM_MODEL
    if SLM_MODEL is not None:
        return True
    
    try:
        from llama_cpp import Llama
        MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "qwen2.5-0.5b-instruct-q4_k_m.gguf")
        
        if os.path.exists(MODEL_PATH):
            print(f"Loading Offline AI from {MODEL_PATH}...")
            # n_ctx=1024 to save RAM, n_gpu_layers=0 for 100% pure CPU execution
            SLM_MODEL = Llama(model_path=MODEL_PATH, n_ctx=1024, verbose=False, n_gpu_layers=0)
            return True
        else:
            return False
    except ImportError:
        return False

async def fetch_llm_classification(title, text):
    if not init_slm():
        return None, None
        
    prompt = f"""<|im_start|>system
You are a data extractor. Output ONLY valid JSON containing "category" and "location". No other text.
Categories: "Traffic", "Fire", "Electricity", "Theft", "Culture".
Location: A Kocaeli district (e.g., "İzmit", "Gebze") or "Kocaeli (Merkez)".<|im_end|>
<|im_start|>user
Title: {title}
Content: {text[:600]}<|im_end|>
<|im_start|>assistant
{{"""
    try:
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(None, lambda: SLM_MODEL(
            prompt,
            max_tokens=60,
            stop=["<|im_end|>", "}"],
            temperature=0.0
        ))
        
        res_text = "{" + output['choices'][0]['text'].strip()
        if not res_text.endswith("}"):
            res_text += "}"
            
        res = json.loads(res_text)
        return res.get("category"), res.get("location")
    except Exception:
        return None, None

async def process_nlp_for_articles(articles, existing_db_articles=None):
    if existing_db_articles is None:
        existing_db_articles = []
        
    print("Starting Async SLM NLP Classification & Semantic Embedding loop...")
    
    accepted_corpus = list(existing_db_articles)
    processed_items = []
    vectorizer = TfidfVectorizer()
    
    # CRITICAL BUG FIX: We MUST pre-fit the TF-IDF vocabulary using ALL articles (existing + new) AT ONCE.
    # Otherwise, it incrementally fits on single documents, causing bizarre 99% similarity matches on unrelated words!
    all_texts = [a["raw_content"] for a in accepted_corpus] + [a["raw_content"] for a in articles]
    if all_texts:
        vectorizer.fit(all_texts)
    
    for item in articles:
        # Step 1: Semantic Embedding Duplicate Detection (>= 90% threshold)
        if hasattr(vectorizer, 'vocabulary_') and accepted_corpus:
            new_vec = vectorizer.transform([item["raw_content"]])
            max_sim = 0
            matched_original = None
            
            for accepted in accepted_corpus:
                # PDF SPECIFICATION: Duplicates only logically occur transversally across DIFFERENT newspapers.
                if accepted.get("source") == item.get("source"):
                    continue
                    
                acc_vec = vectorizer.transform([accepted["raw_content"]])
                sim = cosine_similarity(new_vec, acc_vec)[0][0]
                if sim > max_sim:
                    max_sim = sim
                    matched_original = accepted
                    
            # TEMPORARY FIX: Lowered specifically to 0.15 just so you can test the UI Modal right now!
            # You should change this back to 0.90 before submitting the project!
            if max_sim >= 0.90:
                print(f"[NLP] DUP REJECTED ({int(max_sim*100)}%): '{item['title']}' matches original.")
                item["is_duplicate"] = True
                
                # We save WHAT article it duplicated with so the backend can merge them later
                item["duplicate_of_link"] = matched_original["link"]
                processed_items.append(item)
                continue

        # Step 2: Push totally unique articles strictly through the LLM
        cat, location = await fetch_llm_classification(item["title"], item["raw_content"])
        
        item["category"] = cat if cat else fallback_classify(item["raw_content"], item["title"])
        item["location"] = location if location else fallback_location(item["raw_content"])

        # Important: Setup the multi-source string array capability for the UI design
        item["sources"] = [item["source"]]

        accepted_corpus.append(item)
        vectorizer.fit([a["raw_content"] for a in accepted_corpus])
        processed_items.append(item)
        
    return processed_items
