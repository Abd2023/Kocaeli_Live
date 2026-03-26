import os
import re
import json
import logging
import asyncio
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
import torch

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
    
    # Negative Penalization
    NEGATIVE_KEYWORDS = ["hakem", "milletvekili", "kredi", "spor", "maç", "siyaset", "başkan", "transfer", "konut", "toki", "borsa"]
    penalty = 0
    for kw in NEGATIVE_KEYWORDS:
        if kw in combined:
            penalty += 2
            
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in combined: scores[cat] += 1
            
    for cat in scores:
        scores[cat] -= penalty
        
    best_cat = max(scores, key=scores.get)
    if scores[best_cat] >= 1:
        return best_cat
    else:
        return "Diğer"

#def fallback_location(text, title=""):
#    combined = (title + " " + text).lower()
#    for d in DISTRICTS:
#        if d.lower() in combined.replace('i̇', 'i').replace('ı', 'I'):
#            return d
#    return None

# ---------- ZERO-SHOT CLASSIFIER INTEGRATION ----------- #

ZeroShotClassifier = None

def init_zeroshot():
    global ZeroShotClassifier
    if ZeroShotClassifier is not None:
        return True
    
    try:
        print("Loading Zero-Shot Classifier (MoritzLaurer/mDeBERTa-v3-base-mnli-xnli)...")
        device = 0 if torch.cuda.is_available() else -1
        if device == 0:
            print("=> CUDA detected! Loading NLP Model onto GPU (RTX 4060)...")
        else:
            print("=> CUDA not detected! Loading NLP Model onto CPU...")
            
        ZeroShotClassifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli", device=device)
        return True
    except ImportError:
        print("transformers library missing.")
        return False
    except Exception as e:
        print(f"Failed to load classifier: {e}")
        return False

async def classify_news_zeroshot_async(text: str):
    if not init_zeroshot():
        return "DISCARD"
        
    candidate_labels = [
        "Trafik Kazası", 
        "Yangın", 
        "Elektrik Kesintisi", 
        "Hırsızlık", 
        "Kültürel Etkinlik", 
        "Siyaset, Spor veya Diğer İlgisiz Haberler"
    ]
    hypothesis_template = "Bu metin {} hakkındadır."
    
    loop = asyncio.get_event_loop()
    
    # We truncate text to roughly 1500 chars to avoid memory issues and speed up classification
    truncated_text = text[:1500]
    
    def run_pipeline():
        return ZeroShotClassifier(truncated_text, candidate_labels, hypothesis_template=hypothesis_template)
        
    try:
        result = await loop.run_in_executor(None, run_pipeline)
        
        top_category = result['labels'][0]
        top_score = result['scores'][0]
        
        if top_category == "Siyaset, Spor veya Diğer İlgisiz Haberler" or top_score < 0.40:
            return "DISCARD"
            
        category_map = {
            "Trafik Kazası": "Traffic",
            "Yangın": "Fire",
            "Elektrik Kesintisi": "Electricity",
            "Hırsızlık": "Theft",
            "Kültürel Etkinlik": "Culture"
        }
        
        return category_map.get(top_category, "DISCARD")
    except Exception as e:
        print(f"Zero-Shot classification failed: {e}")
        return "DISCARD"

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
                    
            # Proje Dökümanı Kuralı: %90 ve üzeri benzerlikler aynı haber (kopya) kabul edilir
            if max_sim >= 0.90:
                print(f"[NLP] DUP REJECTED ({int(max_sim*100)}%): '{item['title']}' matches original.")
                item["is_duplicate"] = True
                
                # We save WHAT article it duplicated with so the backend can merge them later
                item["duplicate_of_link"] = matched_original["link"]
                processed_items.append(item)
                continue

        # Step 2: Push totally unique articles strictly through the Zero-Shot Classifier
        cat = await classify_news_zeroshot_async(item["title"] + " " + item["raw_content"])
        
        item["category"] = cat if cat != "DISCARD" else fallback_classify(item["raw_content"], item["title"])
        
        if item["category"] == "Diğer" or item["category"] == "DISCARD":
            print(f"[NLP] REJECTED (İlgisiz): '{item['title']}' is classified as Diğer/Discard.")
            continue
            
        #loc = fallback_location(item["raw_content"], item["title"])
        #if loc is None:
        #    print(f"[NLP] REJECTED (Konum Yok): '{item['title']}' is discarded due to no location.")
        #    continue
        item["location"] = loc

        # Important: Setup the multi-source string array capability for the UI design
        item["sources"] = [item["source"]]

        accepted_corpus.append(item)
        vectorizer.fit([a["raw_content"] for a in accepted_corpus])
        processed_items.append(item)
        
    return processed_items
