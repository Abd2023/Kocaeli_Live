from quart import Quart, jsonify
from quart_cors import cors
from core.database import db
from modules.scraper import run_all_scrapers
from modules.nlp import process_nlp_for_articles

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
        # Take a subset to quickly test NLP processing + duplicate generation logic
        articles = articles[:8] 
        # Add a fake duplicate intentionally to test TF-IDF
        if articles:
            articles.append(articles[0].copy())
            
        processed = await process_nlp_for_articles(articles)
        return jsonify({"status": "success", "count": len(processed), "data": processed})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
