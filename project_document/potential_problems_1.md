# Potential Problems and Solutions for Kocaeli Live Project (Modern 2024 Technologies)

After closely evaluating the most recently created libraries in 2024, our traditional approaches (like BeautifulSoup, TF-IDF, and simple caching) have been entirely replaced with state-of-the-art intelligent tools.

## 1. Web Scraping Challenges (Changing HTML & Anti-Bot Systems)
- **Problem:** Writing CSS selectors (`soup.find(...)`) is incredibly fragile. Local news sites often change layouts, and maintaining 5 different scraper scripts is painful.
  - **Modern 2024 Solution:** We will use **Crawl4AI** or **ScrapeGraphAI**. These are very new, neural-based, LLM-powered scraping libraries released this year. They *do not rely on brittle HTML selectors*. Instead, you provide a schema (e.g., "Extract Title, Article Body, and Publish Date"), and the AI natively parses the entire DOM, understands context, bypasses bot protections, and outputs perfectly structured JSON data.

## 2. Natural Language Processing (NLP) Challenges
- **Problem:** Extracting the perfect neighborhood from unstructured Turkish news text and cleanly classifying it into the 5 categories is too complex for basic regex or older models like `spaCy`.
  - **Modern 2024 Solution:** We will leverage an **LLM via API** (such as Google Gemini, OpenAI `gpt-4o-mini`, or a local model via Ollama). Processing the scraped text through an LLM prompt requesting structured output allows it to flawlessly identify Kocaeli districts and properly classify the event type with zero training data required.
- **Problem:** Duplicate Detection (matching exact story across different sites to enforce the >= 90% threshold).
  - **Modern 2024 Solution:** Instead of TF-IDF, which only looks at word overlap, we will use modern 2024 semantic embedding models (like Hugging Face `multilingual-e5-large` or `text-embedding-3-small`). This computes semantic similarity *by meaning* far more accurately and efficiently.

## 3. Google Maps & Geocoding Costs
- **Problem:** The project mentions using a service "like Google Geocoding API," but Google's APIs are notoriously expensive and restrict how you use external map interfaces.
  - **Modern 2024 Solution:** We can use **Radar** (enterprise-grade, very generous free tier with up to 90% cheaper pricing) or **Mapbox** Geocoding. Mapbox integrates beautifully with React (via `react-map-gl`). Alternatively, if a 100% free solution is preferred, **OpenCage** or **Geoapify** rely on OpenStreetMap data and will easily handle Kocaeli's districts at zero cost.

## 4. Architecture & Flask Constraints
- **Problem:** Python's Flask is a synchronous framework by default. Processing LLM requests, AI scrapers, and embeddings for tons of news concurrently will freeze the web server and block the React frontend.
  - **Modern 2024 Solution:** Since you chose Flask, we will build this using **Quart**, which is the official Pallets project's async equivalent to Flask. Quart uses the exact same `app.route()` syntax but fully supports Python's new `asyncio` (`async def`). This perfectly handles concurrent AI scraping and Geocoding without choking a single thread, and perfectly pairs with a modern asynchronous React Vite app.

---
**Summary:** By pairing React with Quart (Async Flask) and supercharging our data extraction pipeline with Crawl4AI/ScrapeGraphAI and lightweight LLMs, we will build a vastly more resilient, scalable, and genuinely intelligent architecture that eliminates 90% of the manual maintenance associated with older projects.
