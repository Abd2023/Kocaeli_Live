# Potential Problems and Solutions for Kocaeli Live Project

Before we proceed with creating a detailed Step-by-Step Implementation Plan for the Flask + React application, here is a breakdown of the key challenges we anticipate encountering and the strategies we will use to solve them.

## 1. Web Scraping Challenges
- **Problem: Anti-Scraping Measures & Blocks.** News websites often use Cloudflare or rate-limiting to block automated requests.
  - **Solution:** We will use the `requests` library with rotating `User-Agent` headers. If a site relies heavily on JavaScript rendering and blocks basic HTTP requests, we will escalate to using `Playwright` instead of `BeautifulSoup4`.
- **Problem: Changing HTML Structures.** News sites frequently update their layouts (class names, tags), which breaks scrapers.
  - **Solution:** We will implement the scraper using the **Adapter Pattern**. Each website will have its own dedicated scraping class with robust selectors (e.g., targeting specific semantic tags or `id` attributes rather than complex, brittle CSS paths).
- **Problem: Scraping Duplicate Data Across Runs.** The system needs to run automatically and not insert the exact same article multiple times.
  - **Solution:** We will use the article's unique URL as an index in MongoDB to enforce uniqueness at the database level.

## 2. Natural Language Processing (NLP) Challenges
- **Problem: Accurate Turkish Location Extraction (NER).** Extracting the exact neighborhood or district from unstructured Turkish text is difficult.
  - **Solution:** We will build a comprehensive keyword dictionary containing all of Kocaeli's districts and prominent neighborhoods. If a simple dictionary match fails, we can fall back on a library like `spaCy` (using a Turkish model) to extract general location entities.
- **Problem: Semantic Text Similarity (>= 90%).** The project requires identifying if two news articles from different sources talk about the *exact* same event based on a 90% similarity threshold.
  - **Solution:** We will use the `scikit-learn` library to apply **TF-IDF Vectorization** and compute **Cosine Similarity** between texts. If TF-IDF is not accurate enough, we can switch to a pre-trained multilingual embedding model using `sentence-transformers` (e.g., `paraphrase-multilingual-MiniLM-L12-v2`).
- **Problem: Removing Ads and Boilerplate from Content.** Directly scraping `<div class="content">` might capture intrusive ads or "read also" links.
  - **Solution:** We will write clean-up functions that explicitly filter out `<script>`, `<style>`, and known advertisement widget class names (`div.ad`, `div.banner`) before extracting text.

## 3. Google Maps & Geocoding Challenges
- **Problem: High Usage of Google Geocoding API.** Calling the Geocoding API for every news article could quickly drain the free tier quota or incur costs.
  - **Solution:** We will implement a **Database Cache for Locations**. Before calling the API, the system will check a `Geocache` collection in MongoDB to see if we've already resolved coordinates for the text "İzmit, Kocaeli", for instance.
- **Problem: Resolving Locations Outside Kocaeli.** The Geocoding API might mistake a neighborhood name for a place in a different city or country.
  - **Solution:** We will append ", Kocaeli, Turkey" to all our Geocoding queries to ensure relevance. We will also validate that the returned coordinates fall within the geographical bounding box of Kocaeli.

## 4. Architecture & Frontend Challenges
- **Problem: Cross-Origin Resource Sharing (CORS).** Running a Python Flask backend (e.g., on port 5000) and a React frontend (e.g., on port 5173) simultaneously leads to CORS errors in the browser.
  - **Solution:** We will use the `Flask-CORS` extension in our backend to properly allow API requests from the React frontend running locally.
- **Problem: Flask is Synchronous.** Heavy NLP operations or database queries could block the Flask server since it is single-threaded and synchronous by default.
  - **Solution:** We will keep our NLP functions optimized. If scraping is triggered via an API call, we can handle it asynchronously using Python's `threading` or `concurrent.futures`, or simply run scraping as a separate background process/cron job that directly writes to MongoDB.
- **Problem: Huge MongoDB payloads.** Sending thousands of news records over the API could slow down the React app.
  - **Solution:** We will implement pagination and server-side filtering so the React frontend only fetches the data for the selected filters (e.g., only "Traffic Accidents" from "Gebze").

---
**Summary:** By building specific adapters for scrapers, using TF-IDF for similarity, caching Geolocation results, and organizing Flask properly, we can cleanly avoid the main pitfalls of the project.
