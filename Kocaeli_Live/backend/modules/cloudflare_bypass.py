from seleniumbase import Driver
import time
from urllib.parse import urlparse

# Global cache to reuse cookies across requests
cookie_cache = {}
global_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"

def harvest_cloudflare_cookies(domains):
    """
    Spins up a headed Chrome instance safely using SeleniumBase UC mode,
    navigates to each strictly protected domain, solves Turnstile, 
    and saves the cf_clearance cookie.
    """
    global global_ua
    print("\n--- [Cloudflare Bypass] Spinning up SeleniumBase Harvester ---")
    
    # UC mode to bypass Cloudflare. Headless is easily detected, so we use headed for the 10 sec harvest.
    try:
        driver = Driver(uc=True, headless=False)
    except Exception as e:
        print(f"Failed to start SeleniumBase driver: {e}")
        return False
        
    harvested_count = 0
    try:
        for domain in domains:
            print(f"Harvesting clearance for {domain}...")
            driver.uc_open_with_reconnect(domain, 4)
            
            # Explicitly attempt to click Turnstile if it pops up
            try:
                driver.uc_gui_click_captcha()
                print(" Clicked Turnstile widget.")
            except Exception:
                pass
                
            # Wait for redirect
            time.sleep(5)
            
            cookies = driver.get_cookies()
            cf_clearance = None
            for cookie in cookies:
                if cookie['name'] == 'cf_clearance':
                    cf_clearance = cookie['value']
            
            if cf_clearance:
                domain_key = urlparse(domain).netloc.replace('www.', '')
                cookie_cache[domain_key] = cf_clearance
                print(f" Successfully harvested cf_clearance for {domain_key}")
                harvested_count += 1
            else:
                print(f" Failed to find cf_clearance for {domain}. They might have IP banned us or loading was too slow.")
                
        # Update user agent from the exact browser that solved the challenge
        global_ua = driver.execute_script("return navigator.userAgent;")
    except Exception as e:
        print(f"Error during harvesting: {e}")
    finally:
        driver.quit()
        
    print(f"--- [Cloudflare Bypass] Harvested {harvested_count}/{len(domains)} cookies ---\n")
    return harvested_count > 0

def get_bypass_headers(url):
    """Returns headers including the valid cf_clearance cookie if harvested."""
    headers = {
        'User-Agent': global_ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    domain_key = urlparse(url).netloc.replace('www.', '')
    if domain_key in cookie_cache:
        headers['Cookie'] = f"cf_clearance={cookie_cache[domain_key]}"
        
    return headers

def is_cookie_valid(domain_url):
    domain_key = urlparse(domain_url).netloc.replace('www.', '')
    return domain_key in cookie_cache
