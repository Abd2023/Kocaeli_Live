import os
import asyncio
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
import modules.cloudflare_bypass as cb

import cloudscraper

# Use robust cloudscraper to bypass Cloudflare/403s instead of raw aiohttp
scraper_client = cloudscraper.create_scraper()


# Sınırlandırıcı (Semaphore) - Aynı anda en fazla 3 istek atılmasını sağlar
# fetch_semaphore = asyncio.Semaphore(3)

async def fetch_html(session, url):
    #  Ağ trafiğini kilitleyerek sitelere DDoS atmayı engelle
    # async with fetch_semaphore:
    try:
        def req():
            headers = cb.get_bypass_headers(url)
            return scraper_client.get(url, headers=headers, timeout=15)
        
        # İnsan davranışını taklit etmek için 1 saniye beklet
        # await asyncio.sleep(1) 
        
        response = await asyncio.to_thread(req)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def extract_article_links(html, base_url, current_url):
    soup = BeautifulSoup(html, 'html.parser')
    seen_links = set()
    ordered_links = []
    blacklist = ['/spor', '/siyaset', '/ekonomi', '/magazin', '/yazarlar', '/dunya', 'haberleri', 'kategori', '/galeri', '/video', '/kurumsal', '/iletisim', '/kunye']
    
    base_domain = urlparse(base_url).netloc.replace('www.', '')
    
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        
        # Safely resolve relative URLs
        href = urljoin(base_url, href)
        parsed = urlparse(href)
        
        if base_domain not in parsed.netloc:
            continue
            
        is_blacklisted = False
        for b in blacklist:
            if b in parsed.path.lower():
                is_blacklisted = True
                break
        if is_blacklisted:
            continue
            
        if href == current_url or href == current_url + "/":
            continue
            
        if len(parsed.path) > 20:
            # Most article slugs have multiple words separated by dashes.
            if parsed.path.count('-') >= 3 or (parsed.path.count('-') >= 1 and any(char.isdigit() for char in parsed.path)):
                if not href.lower().endswith(('.jpg', '.png', '.jpeg', '.pdf', '.gif', '.mp4', '.svg', '.webp')):
                    if href not in seen_links:
                        seen_links.add(href)
                        ordered_links.append(href)
    return ordered_links[:30] # Grab more links to guarantee we find at least 10 recent ones

def extract_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    for el in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        el.extract()
        
    paragraphs = soup.find_all('p')
    # Strictly use paragraph tags. Do not fall back to get_text() as it brings in sidebars.
    valid_p = [p.get_text(separator=' ', strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]
    text = ' '.join(valid_p)
        
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return '\n'.join(chunk for chunk in chunks if chunk)

def is_within_3_days(date_str):
    if not date_str:
        return True # Fallback: Assume recent since many local sites lack proper meta tags
    try:
        date_str = date_str.replace('Z', '+00:00')
        article_date = datetime.fromisoformat(date_str)
        if article_date.tzinfo is None:
            article_date = article_date.replace(tzinfo=timezone.utc)
            
        diff = datetime.now(timezone.utc) - article_date
        return diff.days <= 3
    except Exception:
        return True # Fallback on bizarre date formats

async def scrape_source(session, source_name, url, base_url):
    print(f"[{source_name}] Fetching {url}...")
    html = await fetch_html(session, url)
    if not html:
        return []
        
    links = extract_article_links(html, base_url, url)
    print(f"[{source_name}] Found {len(links)} links. Tracking and Filtering 3-Day Window...")
    
    articles = []
    for link in links:
        if len(articles) >= 8: # Cap at 8 successful, recent articles per source URL
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
            
            # Better title extraction
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
            else:
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
        {"name": "cagdaskocaeli", "base_url": "https://www.cagdaskocaeli.com.tr", "urls": ["https://www.cagdaskocaeli.com.tr/kocaeli-asayis-haberleri", "https://www.cagdaskocaeli.com.tr/kultur-sanat", "https://www.cagdaskocaeli.com.tr/guncel"]},
        {"name": "ozgurkocaeli", "base_url": "https://www.ozgurkocaeli.com.tr", "urls": ["https://www.ozgurkocaeli.com.tr/kocaeli-asayis-haberleri", "https://www.ozgurkocaeli.com.tr/guncel", "https://www.ozgurkocaeli.com.tr/kocaeli-asayis-haberleri"]},
        {"name": "seskocaeli", "base_url": "https://www.seskocaeli.com", "urls": ["https://www.seskocaeli.com/kocaeli-asayis-haberleri", "https://www.seskocaeli.com/kocaeli-son-dakika-haberler", "https://www.seskocaeli.com/kocaeli-yasam-haberleri"]},
        {"name": "yenikocaeli", "base_url": "https://yenikocaeli.com", "urls": ["https://www.yenikocaeli.com/haber/polis-adliye.html", "https://www.yenikocaeli.com/haber/guncel.html", "https://www.yenikocaeli.com/haber/yasam.html"]},
        {"name": "bizimyaka", "base_url": "https://www.bizimyaka.com", "urls": ["https://www.bizimyaka.com/kocaeli-asayis-haberleri", "https://www.bizimyaka.com/kocaeli-son-dakika-haberleri", "https://www.bizimyaka.com/yasam-haberleri"]}
    ]
    
    # Pre-harvest clearance cookies for strictly protected domains
    protected_domains = [
        "https://www.cagdaskocaeli.com.tr/",
        "https://www.ozgurkocaeli.com.tr/",
        "https://www.seskocaeli.com/"
    ]
    needs_harvest = any(not cb.is_cookie_valid(d) for d in protected_domains)
    if needs_harvest:
        print("[Cloudflare] Cookie cache empty or expired. Triggering pre-harvest...")
        await asyncio.to_thread(cb.harvest_cloudflare_cookies, protected_domains)
    
    all_articles = []
    # session is dummy now since we use scraper_client
    dummy_session = None
    
    tasks = []
    for src in sources:
        for url in src["urls"]:
            tasks.append(scrape_source(dummy_session, src["name"], url, src["base_url"]))
            
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, list):
            all_articles.extend(r)
        else:
            print(f"A scraper task failed abruptly: {r}")
            
    return all_articles
