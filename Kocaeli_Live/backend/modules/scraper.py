import os
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup

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
            links.add(href)
    return list(links)[:3] # we take 3 articles max per site for this test

def extract_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.extract()
    text = soup.get_text(separator=' ')
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return '\n'.join(chunk for chunk in chunks if chunk)

async def scrape_source(session, source_name, url):
    print(f"[{source_name}] Fetching homepage...")
    html = await fetch_html(session, url)
    if not html: return []
    
    links = extract_article_links(html, url)
    print(f"[{source_name}] Found {len(links)} links. Filtering...")
    
    articles = []
    for link in links:
        art_html = await fetch_html(session, link)
        if art_html:
            raw_content = extract_text(art_html)
            
            # Simple title extraction
            soup = BeautifulSoup(art_html, 'html.parser')
            title = soup.title.string if soup.title else "No Title"

            articles.append({
                "source": source_name,
                "link": link,
                "title": title.strip(),
                "raw_content": raw_content[:500] + "... [TRUNCATED FOR SPEED]",
                "date": datetime.now().isoformat()
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
        results = await asyncio.gather(*tasks)
        for r in results:
            all_articles.extend(r)
            
    return all_articles
