# Kocaeli Live - Step-by-Step Implementation Plan

This document outlines the architecture and execution strategy for the Web Scraping and Map Visualization System. We will follow a strict, step-by-step approach to validate each component independently as requested.

## Proposed Stack & Document Compliance
- **Backend:** Python Quart (Async Flask) - *Compliant (Any language allowed)*
- **Frontend:** React + Tailwind CSS - *Compliant (Any language allowed)*
- **Database:** MongoDB - *MANDATORY per document*
- **Scraping:** Crawl4AI / Custom Scrapers - *Compliant*
- **Map Visualization:** Google Maps JavaScript API - *MANDATORY per document*
- **Geocoding:** OpenCage API / Nominatim (Free) - *Compliant. The project explicitly states "Bir geocoding servisi (Google Geocoding API gibi)", which translates to "A service MUST be used (such as Google Geocoding API)". This clearly permits alternatives.*

## Execution Strategy

### Phase 1: Environment & Architecture Foundations
1. Initialize the Python Quart structure inside `backend/`.
2. Configure basic REST endpoints and CORS.
3. Initialize the React app inside `frontend/` using Vite.
4. Establish the MongoDB connection in the backend and verify read/write.
**Validation:** Both servers run locally, React can fetch a simple "Hello World" from Quart, and Quart can insert a test document into MongoDB.

### Phase 2: Web Scraping Engine
1. Implement scraping logic for the 5 target sites (`cagdaskocaeli.com.tr`, `ozgurkocaeli.com.tr`, `seskocaeli.com`, `yenikocaeli.com`, `bizimyaka.com`).
2. Robustly extract [Title, Raw Content, Date, Source, Link].
3. Expose a `/api/scrape` endpoint to trigger the job.
**Validation:** Running the `/api/scrape` endpoint successfully returns an array of raw news articles without saving.

### Phase 3: NLP, Classification & Duplicate Detection
1. Implement an intelligent NLP pipeline (via LLM function calling or hybrid keyword mapping) to parse Raw Content.
2. Automatically assign the Category (Traffic, Fire, Electricity, Theft, Culture) and extract the Kocaeli District/Neighborhood.
3. Calculate semantic similarity using Embeddings to enforce the >= 90% duplicate rejection rule.
**Validation:** The NLP module reliably outputs the exact Category and Location, and gracefully rejects duplicate stories covering the same physical event.

### Phase 4: Geocoding & Persistence
1. Integrate the OpenCage API to convert extracted Locations (e.g. "İzmit, Kocaeli, Turkey") into precise `[Lat, Lng]`.
2. Implement MongoDB logic to save the fully processed News Article and cache the Geocoded locations to prevent redundant API calls.
**Validation:** End-to-end backend test. Triggering the scraper results in clean, categorized, geolocated documents safely saved in MongoDB.

### Phase 5: UI & Map Integration
1. Build the React Sidebar with Dynamic Filters (Date Range, District Dropdown, Category Pills) to match the provided Figma constraints.
2. Integrate Google Maps JS API.
3. Fetch News from the backend and plot Custom Colored Markers dynamically on the map.
4. Implement Marker InfoWindows containing the Title, Source, Date, and "Habere Git" button.
**Validation:** The UI looks premium. Changing Sidebar filters instantly updates the Map markers without a page refresh.
