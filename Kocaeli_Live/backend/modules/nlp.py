import os
import re
import json
import logging
import asyncio
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
import torch

# Fallbacks just in case the SLM is unavailable
CATEGORIES = {
    "Traffic": ["kaza", "trafik", "çarpış", "devril", "yaralan", "araç", "otomobil", "motosiklet", "sürücü"],
    "Fire": ["yangın", "itfaiye", "alev", "kundaklama", "yandı", "duman", "söndür"],
    "Electricity": ["elektrik", "kesinti", "sedaş", "karanlık", "arıza", "trafo", "enerji"],
    "Theft": ["hırsız", "çaldı", "çalıntı", "soygun", "gasp", "hırsızlık", "çalan"],
    "Culture": ["etkinlik", "konser", "festival", "fuar", "sergi", "tiyatro", "gösteri", "sahne", "orkestra"]
}

DISTRICTS = [
    "İzmit", "Gebze", "Gölcük", "Karamürsel", 
    "Körfez", "Derince", "Kartepe", "Başiskele", 
    "Çayırova", "Darıca", "Dilovası", "Kandıra"
]

# Keywords that indicate an article is NOT one of the 5 valid categories
VIOLENCE_KEYWORDS = ["cinayet", "öldür", "öldü", "bıçak", "bıçakla", "silah", "tabanca",
                     "kavga", "darp", "darbetti", "şiddet", "infaz", "ceset", "hayatını kaybetti"]
IRRELEVANT_KEYWORDS = ["hakem", "milletvekili", "kredi", "spor", "maç", "siyaset",
                       "başkan", "transfer", "konut", "toki", "borsa", "seçim", "meclis",
                       "kar yağışı", "kar sürpriz", "hava durumu", "deprem", "sel", "fırtına",
                       "yağmur", "mahsur kalan", "beyaza büründü"]

def fallback_classify(text, title=""):
    combined = (title + " " + text).lower()
    scores = {cat: 0 for cat in CATEGORIES}
    
    # Count violence keywords — if DOMINANT, immediately reject
    violence_count = sum(1 for kw in VIOLENCE_KEYWORDS if kw in combined)
    if violence_count >= 2:
        return "Diğer"  # Block stabbings/murders from getting any category
    
    # Count weather/irrelevant keywords — if DOMINANT, immediately reject
    irrelevant_count = sum(1 for kw in IRRELEVANT_KEYWORDS if kw in combined)
    if irrelevant_count >= 2:
        return "Diğer"
    
    # Heavy penalty for violence/crime content (should not be classified as Theft)
    violence_penalty = violence_count * 3
    
    # General irrelevant penalty
    irrelevant_penalty = irrelevant_count * 2
            
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in combined: scores[cat] += 1
    
    # Apply violence penalty specifically to Theft (murders are not theft)
    scores["Theft"] -= violence_penalty
    
    # Apply general irrelevant penalty to all categories
    for cat in scores:
        scores[cat] -= irrelevant_penalty
        
    best_cat = max(scores, key=scores.get)
    if scores[best_cat] >= 1:
        return best_cat
    else:
        return "Diğer"

def _normalize_turkish(text):
    """Normalize Turkish text for reliable case-insensitive matching.
    Handles İ/i, I/ı, Ş/ş, Ç/ç, Ğ/ğ, Ö/ö, Ü/ü properly."""
    # NFC normalize first to handle combining characters
    text = unicodedata.normalize('NFC', text)
    # Turkish-aware lowering: İ→i, I→ı (but we want ASCII-ish matching)
    text = text.replace('İ', 'i').replace('I', 'i')
    text = text.replace('ı', 'i').replace('i̇', 'i')  # combining dot-above variant
    return text.lower()

def fallback_location(text, title=""):
    combined = _normalize_turkish(title + " " + text)
    for d in DISTRICTS:
        normalized_district = _normalize_turkish(d)
        if normalized_district in combined:
            return d
    return None

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
        
    # Expanded labels: 5 valid categories + 5 explicit negative categories
    # This gives the model clearer choices so it doesn't force-fit
    # murders into "Hırsızlık" or weather into "Kültürel Etkinlik"
    candidate_labels = [
        "Trafik Kazası", 
        "Yangın", 
        "Elektrik Kesintisi", 
        "Hırsızlık ve Soygun", 
        "Kültürel Etkinlik", 
        "Cinayet, Kavga veya Şiddet Olayı",
        "Hava Durumu veya Doğa Olayı",
        "Siyaset veya Ekonomi Haberi",
        "Spor Haberi",
        "Genel Haber"
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
        
        # Only map the 5 valid project categories; everything else is DISCARD
        category_map = {
            "Trafik Kazası": "Traffic",
            "Yangın": "Fire",
            "Elektrik Kesintisi": "Electricity",
            "Hırsızlık ve Soygun": "Theft",
            "Kültürel Etkinlik": "Culture"
        }
        
        # If the top label is not one of our 5 categories, discard immediately
        # Return DISCARD:reason so the pipeline knows NOT to try the fallback
        if top_category not in category_map:
            print(f"[NLP] Zero-Shot → '{top_category}' ({top_score:.0%}) — not a valid category, DISCARDING")
            return f"DISCARD:{top_category}"
        
        # If confidence is too low even for a valid category, discard
        if top_score < 0.35:
            print(f"[NLP] Zero-Shot → '{top_category}' ({top_score:.0%}) — confidence too low, DISCARDING")
            return "DISCARD"
        
        print(f"[NLP] Zero-Shot → '{top_category}' ({top_score:.0%}) — ACCEPTED as {category_map[top_category]}")
        return category_map[top_category]
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
        
        # If zero-shot confidently identified it as an INVALID category (e.g. violence, weather, politics)
        # do NOT fall back to keywords — the AI's judgment is more reliable here
        if cat.startswith("DISCARD:"):
            reason = cat.split(":", 1)[1]
            print(f"[NLP] REJECTED (AI → {reason}): '{item['title']}' — skipping keyword fallback")
            continue
        
        # Only use keyword fallback when zero-shot had LOW confidence (generic DISCARD)
        if cat == "DISCARD":
            cat = fallback_classify(item["raw_content"], item["title"])
        
        item["category"] = cat
        
        if item["category"] == "Diğer" or item["category"] == "DISCARD":
            print(f"[NLP] REJECTED (İlgisiz): '{item['title']}' is classified as Diğer/Discard.")
            continue
            
        loc = fallback_location(item["raw_content"], item["title"])
        if loc is None:
            print(f"[NLP] REJECTED (Konum Yok): '{item['title']}' is discarded due to no location.")
            continue
        item["location"] = loc

        # Important: Setup the multi-source string array capability for the UI design
        item["sources"] = [item["source"]]

        accepted_corpus.append(item)
        vectorizer.fit([a["raw_content"] for a in accepted_corpus])
        processed_items.append(item)
        
    return processed_items
