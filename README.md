# Kocaeli Live — Intelligent Urban News Monitor

> A full-stack, AI-powered web platform that automatically scrapes, classifies, and maps local breaking news across the **Kocaeli** province in real-time.

![Kocaeli Live Homepage](./docs/homepage.png)

---

## 📋 Table of Contents

- [About the Project](#-about-the-project)
- [Key Features](#-key-features)
- [Project Architecture](#%EF%B8%8F-project-architecture)
- [Tech Stack](#-tech-stack)
- [Installation & Setup](#%EF%B8%8F-installation--setup)
- [Environment Variables](#-environment-variables)
- [How It Works](#-how-it-works)
- [API Endpoints](#-api-endpoints)

---

## 🧠 About the Project

**Kocaeli Live** is an open-source urban intelligence platform built for *Kocaeli University — Software Laboratory II (Spring 2026)*. It continuously monitors 5 major local Kocaeli news outlets, processes each article through a fully offline local Language Model, and pins each event onto an interactive Google Map — all in real-time.

The system is designed around three core pillars:
1. **Speed** — Fully asynchronous Python backend scrapes all 5 news sources in parallel with `asyncio + aiohttp`.
2. **Intelligence** — The `Qwen2.5-0.5B-Instruct` Small Language Model (SLM) runs entirely offline to extract event categories and precise district names from raw Turkish-language article text.
3. **Accuracy** — A TF-IDF cosine-similarity engine detects and merges duplicate news reported across multiple outlets into a single canonical entry, building a transparent source list.

---

## 🚀 Key Features

| Feature | Description |
|---|---|
| 🕷️ **Async Web Scraper** | Scrapes 5 local news sites simultaneously with a 3-day freshness window |
| 🤖 **Offline AI Classification** | Local Qwen LLM extracts **Category** and **District** from raw Turkish text — zero internet required |
| 🔁 **Duplicate Detection & Merging** | TF-IDF cosine similarity detects identical news across sources and merges their URLs into one entry |
| 📍 **Smart Geocoding** | OpenCage API converts extracted district names into GPS coordinates with MongoDB caching |
| 🗺️ **Interactive Live Map** | Custom SVG category-icon markers (🚗 Trafik, 🔥 Yangın, ⚡ Elektrik, 🛡️ Hırsızlık, 🎵 Kültür) |
| 🔍 **Smart Filtering** | Filter map and news feed by category, district, and date — apply explicitly with the **Filtrele** button |
| 📰 **Scrollable News Feed** | Sidebar "Son Haberler" feed with hover → map pin highlight interaction |
| 👯 **Duplicate Report Modal** | One-click report showing all duplicate news with links to each source website |

---

## 🏗️ Project Architecture

```
yazlab_1/
│
├── README.md
├── docs/
│   └── homepage.png          # UI Screenshot
│
└── Kocaeli_Live/
    │
    ├── backend/              # Python Async API Server
    │   ├── app.py            # Quart routes: /api/news, /api/sync-news
    │   ├── requirements.txt
    │   └── modules/
    │       ├── scraper.py    # Async aiohttp + BeautifulSoup4 scraper (5 sources)
    │       ├── nlp.py        # TF-IDF duplicate engine + Qwen LLM classifier
    │       └── geocoder.py   # OpenCage API with MongoDB caching layer
    │
    └── frontend/             # React 18 + Vite SPA
        ├── public/
        ├── src/
        │   ├── App.jsx           # Root layout, state management, filters
        │   └── components/
        │       ├── Sidebar.jsx         # Filter panel + Son Haberler feed
        │       ├── MapView.jsx         # Google Maps + AdvancedMarker SVG pins
        │       └── DuplicateReportModal.jsx  # Duplicate news report overlay
        └── .env              # VITE_GOOGLE_MAPS_API_KEY
```

### Data Flow Diagram

```
   ┌──────────────┐     HTTP GET      ┌─────────────────────────┐
   │  React SPA   │ ─────────────────▶│   Quart Backend (5000)  │
   │  (Vite:5173) │                   │      app.py             │
   └──────┬───────┘                   └────────┬────────────────┘
          │                                    │
     Render Map                        ┌───────▼────────┐
     + Sidebar Feed                    │   scraper.py   │  ← aiohttp async
                                       │  5 news sites  │
                                       └───────┬────────┘
                                               │ raw articles
                                       ┌───────▼────────┐
                                       │    nlp.py      │  ← Qwen LLM (offline)
                                       │  TF-IDF Dedupe │     + TF-IDF cosine
                                       └───────┬────────┘
                                               │ classified articles
                                       ┌───────▼────────┐
                                       │  geocoder.py   │  ← OpenCage API
                                       │  MongoDB Cache │
                                       └───────┬────────┘
                                               │ lat/lng added
                                       ┌───────▼────────┐
                                       │    MongoDB     │  ← Motor (async driver)
                                       └────────────────┘
```

---

## 🛠️ Tech Stack

**Backend**
- [Python Quart](https://quart.palletsprojects.com/) — Async web framework (equivalent to Flask but fully async)
- [Motor](https://motor.readthedocs.io/) — Async MongoDB driver
- [aiohttp](https://docs.aiohttp.org/) + [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — Async web scraping
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) — Local LLM inference (Qwen2.5-0.5B-Instruct)
- [scikit-learn](https://scikit-learn.org/) — TF-IDF vectorizer + cosine similarity

**Frontend**
- [React 18](https://react.dev/) + [Vite](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [@vis.gl/react-google-maps](https://visgl.github.io/react-google-maps/)
- [Lucide React](https://lucide.dev/) — SVG icon library
- [date-fns](https://date-fns.org/) — Turkish-locale date formatting

**Database & APIs**
- [MongoDB](https://www.mongodb.com/) — Primary data store
- [OpenCage Geocoding API](https://opencagedata.com/) — District → GPS coordinate conversion
- [Google Maps JavaScript API](https://developers.google.com/maps) — Interactive map rendering

---

## ⚙️ Installation & Setup

> **Prerequisites:** Python 3.10+, Node.js 18+, MongoDB running locally or via Atlas, API keys for OpenCage and Google Maps.

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/yazlab_1.git
cd yazlab_1/Kocaeli_Live
```

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install Python dependencies
pip install -r requirements.txt

# Create .env file (see Environment Variables section below)
copy .env.example .env

# Download the Qwen LLM model automatically (~490 MB, one-time only)
python setup_model.py

# Start the backend server
python app.py
```
The API will be live at **http://localhost:5000**

> **Note on the AI Model:** The `Qwen2.5-0.5B-Instruct-Q4_K_M.gguf` model is **not included** in this repository (it's ~490 MB). Run `python setup_model.py` once and it will automatically download directly from Hugging Face into the `backend/models/` directory.

### 3. Frontend Setup
```bash
cd ../frontend

# Install Node dependencies
npm install

# Create frontend .env file
echo "VITE_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here" > .env

# Start the dev server
npm run dev
```
The UI will open at **http://localhost:5173**

---

## 🔐 Environment Variables

### `backend/.env`
```env
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=kocaeli_live
OPENCAGE_API_KEY=your_opencage_api_key_here
```

### `frontend/.env`
```env
VITE_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

> **Get your free API keys:**
> - OpenCage: https://opencagedata.com/api (2,500 free requests/day)
> - Google Maps: https://console.cloud.google.com (requires billing enabled for `AdvancedMarker`)
> - MongoDB: https://www.mongodb.com/atlas/database (free 512MB cluster)

---

## 🔍 How It Works

1. **User clicks "Haberleri Güncelle"** — The React frontend calls `POST /api/sync-news`
2. **Scraper runs** — `scraper.py` fetches the last 10 articles from each of 5 news sites using `aiohttp`, enforcing a 3-day freshness window
3. **NLP processes each article** — `nlp.py` sends each article to the local Qwen LLM, which returns a JSON object with `category` (Traffic / Fire / Electricity / Theft / Culture) and `location` (e.g., "İzmit", "Gebze")
4. **Duplicate detection** — TF-IDF cosine similarity checks each new article against the existing database. If ≥ 90% similar to an existing entry from a different source, the new article's URL is merged into the original's `sources[]` array instead of creating a duplicate entry
5. **Geocoding** — `geocoder.py` converts the extracted location name to GPS coordinates via OpenCage API, with results cached in MongoDB to save API quota
6. **Stored in MongoDB** — The enriched article is saved with title, content, category, location, coordinates, date, and sources list
7. **Map renders** — The React frontend fetches `GET /api/news` and renders each article as a custom SVG map pin colored and iconified by category

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/news` | Returns all stored articles from MongoDB |
| `POST` | `/api/sync-news` | Triggers the full scrape → NLP → geocode → store pipeline |

---

## 👨‍💻 Developed By

Developed by the **Kocaeli University Computer Engineering** team
*Software Laboratory II — Spring 2026 Curriculum*

---

*This is an open-source academic project. Feel free to fork, extend, and build upon it.*
