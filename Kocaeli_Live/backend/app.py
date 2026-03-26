from quart import Quart, jsonify
from quart_cors import cors
from core.database import db
from modules.scraper import run_all_scrapers
from modules.nlp import process_nlp_for_articles
from modules.geocoding import get_coordinates

app = Quart(__name__)
app = cors(app, allow_origin="*") # Allow React connection

@app.route('/api/health', methods=['GET'])
async def health_check():
    try:
        await db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected ({e})"
    return jsonify({"status": "ok", "db": db_status})

@app.route('/api/test-db', methods=['POST'])
async def test_db_insert():
    try:
        result = await db["test_collection"].insert_one({
            "message": "Hello World from Quart!",
            "timestamp": "Now"
        })
        return jsonify({"status": "success", "id": str(result.inserted_id), "message": "Test document inserted into MongoDB!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/scrape', methods=['GET'])
async def test_scrape():
    try:
        articles = await run_all_scrapers()
        return jsonify({"status": "success", "count": len(articles), "data": articles})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/test-nlp', methods=['GET'])
async def test_nlp():
    try:
        articles = await run_all_scrapers()
        articles = articles[:8] 
        if articles:
            articles.append(articles[0].copy())
            
        processed = await process_nlp_for_articles(articles)
        return jsonify({"status": "success", "count": len(processed), "data": processed})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/sync-news', methods=['POST'])
async def sync_news():
    try:
        articles = await run_all_scrapers()
        
        # Pull existing DB history for the Duplicate Analysis corpus
        news_col = db["articles"]
        existing_articles = await news_col.find().to_list(length=500)
        
        processed = await process_nlp_for_articles(articles, existing_db_articles=existing_articles)
        
        saved_count = 0
        merged_count = 0
        
        for item in processed:
            # Handle AI Semantic Duplicates (>= 90%)
            if item.get("is_duplicate") and item.get("duplicate_of_link"):
                await news_col.update_one(
                    {"link": item["duplicate_of_link"]},
                    {"$addToSet": {
                        "sources": item["source"],
                        "duplicate_links": {
                            "source": item["source"],
                            "link": item["link"],
                            "title": item["title"]
                        }
                    }}
                )
                merged_count += 1
                continue
                
            exists = await news_col.find_one({"link": item["link"]})
            if exists:
                continue
                
            lat, lng = await get_coordinates(item["location"])
            if lat is None or lng is None:
                continue
                
            item["lat"] = lat
            item["lng"] = lng
            
            await news_col.insert_one(item)
            saved_count += 1
            
        return jsonify({
            "status": "success", 
            "scraped": len(processed), 
            "saved_new": saved_count,
            "merged_duplicates": merged_count
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/news', methods=['GET'])
async def get_news():
    try:
        news_col = db["articles"]
        cursor = news_col.find().sort("date", -1)
        articles = await cursor.to_list(length=500)
        for a in articles:
            a["_id"] = str(a["_id"]) # JSON serialize the ObjectId
        return jsonify({"status": "success", "data": articles})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
