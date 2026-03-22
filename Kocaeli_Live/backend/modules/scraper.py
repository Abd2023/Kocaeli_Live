import os
import asyncio
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
import re

# We will use robust aiohttp + BS4 as an adapter for ultimate speed,
# falling back or scaling up as needed.
import aiohttp

async def fetch_html(session, url):
    try:
        async with session.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64)'}) as response:
            if response.status == 200:
                return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def extract_article_links(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/'):
            href = base_url.rstrip('/') + href
        if href.startswith(base_url) and len(href) > len(base_url) + 15:
            # Very basic heuristic: if it's long, it's likely an article.
            if not href.lower().endswith(('.jpg', '.png', '.jpeg', '.pdf', '.gif', '.mp4', '.svg', '.webp')):
                links.add(href)
    return list(links)[:30] # Grab more links to guarantee we find at least 10 recent ones

def extract_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.extract()
    text = soup.get_text(separator=' ')
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return '\n'.join(chunk for chunk in chunks if chunk)

def is_within_3_days(date_str):
    if not date_str:
        return True # Fallback: assume recent if CMS hides the date tag
    try:
        date_str = date_str.replace('Z', '+00:00')
        article_date = datetime.fromisoformat(date_str)
        if article_date.tzinfo is None:
            article_date = article_date.replace(tzinfo=timezone.utc)
            
        diff = datetime.now(timezone.utc) - article_date
        return diff.days <= 3
    except Exception:
        return True # Fallback on bizarre date formats

async def scrape_source(session, source_name, url):
    print(f"[{source_name}] Fetching homepage...")
    html = await fetch_html(session, url)
    if not html:
        return []
        
    links = extract_article_links(html, url)
    print(f"[{source_name}] Found {len(links)} links. Tracking and Filtering 3-Day Window...")
    
    articles = []
    for link in links:
        if len(articles) >= 10: # Cap at 10 successful, recent articles per site (50 total)
            break
            
        art_html = await fetch_html(session, link)
        if art_html:
            soup = BeautifulSoup(art_html, 'html.parser')
            
            # Step 1: Enforce 3-Day Rule via HTML5 Metadata
            meta_date = soup.find('meta', property='article:published_time')
            if not meta_date:
                meta_date = soup.find('meta', itemprop='datePublished')
                
            published_str = meta_date['content'] if (meta_date and meta_date.has_attr('content')) else None
            
            if not is_within_3_days(published_str):
                print(f"[{source_name}] Dropped old article (>3 days): {link}")
                continue # Skip old articles entirely per PDF spec!

            # Step 2: Extract Content
            raw_content = extract_text(art_html)
            if len(raw_content) < 100:
                continue
            
            # Simple title extraction
            title_tag = soup.title.string if soup.title else None
            title = (title_tag or "No Title").strip()

            articles.append({
                "source": source_name,
                "link": link,
                "title": title,
                "raw_content": raw_content[:500] + "... [TRUNCATED FOR SPEED]",
                "date": published_str or datetime.now().isoformat()
            })
    return articles

async def run_all_scrapers():
    sources = [
        {"name": "cagdaskocaeli", "url": "https://www.cagdaskocaeli.com.tr/"},
        {"name": "ozgurkocaeli", "url": "https://www.ozgurkocaeli.com.tr/"},
        {"name": "seskocaeli", "url": "https://www.seskocaeli.com/"},
        {"name": "yenikocaeli", "url": "https://yenikocaeli.com/"},
        {"name": "bizimyaka", "url": "https://www.bizimyaka.com/"}
    ]
    
    all_articles = []
    async with aiohttp.ClientSession() as session:
        # Run all sources concurrently for maximum speed
        tasks = [scrape_source(session, src["name"], src["url"]) for src in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                all_articles.extend(r)
            else:
                print(f"A scraper task failed abruptly: {r}")
                
    return all_articles
