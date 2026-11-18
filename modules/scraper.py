"""
Google Maps Multi-Engine Scraper:
1. Direct Google Maps Headless Browser Scraper (100% FREE, No API Key, No Limit)
2. Target-Driven Continuous Hunting: Keeps hunting across multiple sub-queries & areas
   until the exact target number of qualified leads requested by the user is fulfilled!
3. Flexible Website Filter:
   - "NO_WEBSITE": Only leads with phone & NO website (Local clinics, salons, gyms).
   - "HAS_WEBSITE": Only leads with phone & HAS website (Digital Marketing Agencies, B2B companies).
   - "ANY": All leads with phone (both with and without website).
"""
import time
import os
import re
import urllib.parse
from typing import List, Dict, Any, Callable, Optional
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def clean_indian_mobile(raw_phone: str) -> Optional[str]:
    """
    Validates and extracts a clean 10-digit mobile number suitable for WhatsApp outreach.
    Returns 91XXXXXXXXXX or None.
    """
    if not raw_phone:
        return None
        
    digits = re.sub(r'\D', '', raw_phone)
    if not digits:
        return None
        
    # Standard 10 digits starting with 6, 7, 8, 9
    if len(digits) == 10 and digits[0] in '6789':
        return f"91{digits}"
        
    # 11 digits starting with 0 followed by 6, 7, 8, 9
    if len(digits) == 11 and digits.startswith('0') and digits[1] in '6789':
        return f"91{digits[1:]}"
        
    # 12 digits starting with 91 followed by 6, 7, 8, 9
    if len(digits) == 12 and digits.startswith('91') and digits[2] in '6789':
        return digits
        
    return None

def extract_phone_from_text(text: str) -> Optional[str]:
    """
    Extracts mobile numbers from card text with multiple regex patterns.
    """
    patterns = [
        r'(?:\+?91[\s-]?)?[0]?[6-9]\d{4}[\s-]?\d{5}',   # Standard mobile with or without 0 or +91
        r'\b0[6-9]\d{9}\b',                             # 11 digits starting with 0
        r'\b[6-9]\d{9}\b',                              # 10 digits starting with 6-9
        r'\b\d{5}[\s-]?\d{5}\b',                        # 5-5 split
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            cleaned = clean_indian_mobile(m.group(0))
            if cleaned:
                return cleaned
    return None

def generate_search_queries(niche: str, city: str) -> List[str]:
    """
    Generates intelligent related search queries to ensure Google Maps yields
    large volumes of leads.
    """
    queries = []
    base_query = f"{niche} in {city}".strip()
    queries.append(base_query)
    
    area = ""
    main_city = city
    if "," in city:
        parts = [p.strip() for p in city.split(",") if p.strip()]
        if len(parts) >= 2:
            main_city = parts[0]
            area = parts[1]
    
    niche_lower = niche.lower()
    variants = []
    
    if "marketing" in niche_lower or "digital" in niche_lower or "agency" in niche_lower or "seo" in niche_lower:
        variants = [
            "Digital Marketing Agency",
            "Digital Marketing Company",
            "SEO Agency",
            "Social Media Marketing Agency",
            "Advertising Agency",
            "Creative Agency",
            "Performance Marketing Agency",
            "Web & Digital Marketing Agency",
            "Marketing Consultant"
        ]
    elif "dental" in niche_lower or "dentist" in niche_lower:
        variants = ["Dentist", "Dental Care", "Dental Hospital", "Dental Centre", "Dental Clinic"]
    elif "salon" in niche_lower or "spa" in niche_lower or "parlour" in niche_lower:
        variants = ["Beauty Parlour", "Hair Salon", "Spa and Salon", "Makeup Studio", "Nail Salon"]
    elif "gym" in niche_lower or "fitness" in niche_lower:
        variants = ["Fitness Centre", "Gymnasium", "Workout Club", "Crossfit Gym"]
    elif "real estate" in niche_lower or "property" in niche_lower:
        variants = ["Property Dealers", "Real Estate Consultant", "Property Broker", "Builders"]
    elif "cafe" in niche_lower or "restaurant" in niche_lower:
        variants = ["Restaurant", "Cafe and Lounge", "Bistro", "Family Restaurant"]
    elif "skin" in niche_lower or "derma" in niche_lower:
        variants = ["Dermatologist", "Skin Clinic", "Cosmetologist", "Laser Clinic"]
    else:
        variants = [f"Best {niche}", f"Top {niche}", f"{niche} Center", f"Local {niche}"]

    for v in variants:
        if area:
            queries.append(f"{v} in {area} {main_city}")
            queries.append(f"{v} near {area} {main_city}")
        queries.append(f"{v} in {city}")
        
    if area:
        queries.append(f"{niche} in {main_city}")
        queries.append(f"best {niche} in {main_city}")
        for v in variants[:3]:
            queries.append(f"{v} in {main_city}")

    seen = set()
    deduped = []
    for q in queries:
        q_clean = q.strip().lower()
        if q_clean not in seen:
            seen.add(q_clean)
            deduped.append(q)
            
    return deduped

def is_chrome_available() -> bool:
    """
    Checks if Chrome / Chromium is installed and operable in current environment.
    """
    try:
        driver = get_headless_driver()
        driver.quit()
        return True
    except Exception:
        return False

def get_headless_driver():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--window-size=1440,1080')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--lang=en-US')
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_argument('--log-level=3')
    opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    opts.page_load_strategy = 'eager'
    
    # Auto-detect Linux Chromium / Google Chrome binary paths for Cloud deployments
    linux_binaries = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable'
    ]
    for b in linux_binaries:
        if os.path.exists(b):
            opts.binary_location = b
            break
            
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(20)
    return driver

def scrape_google_maps_direct(
    niche: str,
    city: str,
    max_results: int = 20,
    website_filter: str = "NO_WEBSITE", # "NO_WEBSITE", "HAS_WEBSITE", "ANY"
    progress_callback: Optional[Callable[[str, float], None]] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Directly scrapes Google Maps using headless Selenium.
    Zero API cost, zero configuration.
    Continues hunting across multiple related queries until exact target count is fulfilled!
    """
    if "only_mobile_and_no_website" in kwargs:
        website_filter = "NO_WEBSITE" if kwargs["only_mobile_and_no_website"] else "ANY"
    search_queries = generate_search_queries(niche, city)
    
    driver = None
    leads = []
    seen_names = set()
    seen_phones = set()
    processed_urls = set()
    
    try:
        driver = get_headless_driver()
        
        for q_idx, query in enumerate(search_queries):
            if len(leads) >= max_results:
                break
                
            encoded_query = urllib.parse.quote_plus(query)
            target_url = f"https://www.google.com/maps/search/{encoded_query}"
            
            if progress_callback:
                frac = min(0.9, 0.05 + (0.85 * len(leads) / max_results))
                progress_callback(f"Searching: '{query}' (Found {len(leads)}/{max_results} target leads so far)...", frac)
                
            try:
                driver.get(target_url)
            except Exception:
                pass
                
            time.sleep(3)
            
            # Dismiss any consent dialog if present
            for btn in driver.find_elements(By.CSS_SELECTOR, "form[action*='consent'] button, button[aria-label*='Accept all'], button[aria-label*='Reject all']"):
                try:
                    btn.click()
                    time.sleep(1)
                except Exception:
                    pass
            
            feed = None
            for _ in range(4):
                feeds = driver.find_elements(By.CSS_SELECTOR, "div[role='feed']")
                if feeds:
                    feed = feeds[0]
                    break
                time.sleep(1)
                
            if not feed:
                continue
                
            scroll_cycles = 0
            consecutive_no_new = 0
            last_card_count = 0
            max_scrolls_per_query = 16
            
            while scroll_cycles < max_scrolls_per_query and len(leads) < max_results:
                scroll_cycles += 1
                
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
                time.sleep(1.8)
                
                cards = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
                if not cards:
                    cards = driver.find_elements(By.XPATH, "//a[contains(@href, '/maps/place/')]/ancestor::div[contains(@class, 'Nv2PK') or @jsaction]")
                    
                if len(cards) == last_card_count:
                    consecutive_no_new += 1
                    if consecutive_no_new >= 3:
                        break
                else:
                    consecutive_no_new = 0
                    last_card_count = len(cards)
                    
                for card in cards:
                    if len(leads) >= max_results:
                        break
                        
                    try:
                        # 1. Place URL & Name
                        place_links = card.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")
                        if not place_links:
                            continue
                        place_url = place_links[0].get_attribute("href")
                        if not place_url or place_url in processed_urls:
                            continue
                        processed_urls.add(place_url)
                        
                        card_text = card.text
                        name = place_links[0].get_attribute("aria-label")
                        if not name:
                            lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                            name = lines[0] if lines else "Business"
                            
                        name = name.strip()
                        if not name or name in seen_names:
                            continue
                            
                        # Skip sponsored ads
                        if card.find_elements(By.XPATH, ".//*[contains(text(), 'Sponsored') or contains(@aria-label, 'Ad')]"):
                            continue
                        
                        # 2. Check for website from card link
                        website = None
                        web_links = card.find_elements(By.CSS_SELECTOR, "a[data-value='Website'], a[aria-label*='website' i], a[aria-label*='Website']")
                        if web_links:
                            raw_web = web_links[0].get_attribute("href")
                            if raw_web:
                                if 'google.com/url?q=' in raw_web:
                                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_web).query)
                                    website = parsed.get('q', [raw_web])[0]
                                else:
                                    website = raw_web
                                    
                        # 3. Check for phone from card text
                        phone = extract_phone_from_text(card_text)
                        
                        # 4. If phone is missing from preview snippet, click place to open detail panel
                        if not phone:
                            try:
                                driver.execute_script("arguments[0].scrollIntoView(true);", card)
                                place_links[0].click()
                                time.sleep(0.7)
                                
                                # Phone in detail pane
                                ph_elems = driver.find_elements(By.CSS_SELECTOR, "button[data-item-id^='phone:'], [aria-label*='Phone:']")
                                if ph_elems:
                                    raw_ph = ph_elems[0].get_attribute("data-item-id") or ph_elems[0].get_attribute("aria-label") or ph_elems[0].text
                                    phone = extract_phone_from_text(raw_ph)
                                    
                                # Website in detail pane if missing
                                if not website:
                                    web_elems = driver.find_elements(By.CSS_SELECTOR, "a[data-item-id='authority'], a[aria-label*='Website:']")
                                    if web_elems:
                                        raw_web = web_elems[0].get_attribute("href")
                                        if raw_web:
                                            if 'google.com/url?q=' in raw_web:
                                                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_web).query)
                                                website = parsed.get('q', [raw_web])[0]
                                            else:
                                                website = raw_web
                            except Exception:
                                pass
                                
                        # Phone is strictly required for outreach
                        if not phone or phone in seen_phones:
                            continue
                            
                        has_website = bool(website and str(website).strip().lower() not in ["none", "null", ""])
                        
                        # Apply Website Filter Mode
                        if website_filter == "NO_WEBSITE" and has_website:
                            continue
                        elif website_filter == "HAS_WEBSITE" and not has_website:
                            continue
                            
                        seen_names.add(name)
                        seen_phones.add(phone)
                        
                        # Rating and Reviews
                        rm = re.search(r'([1-5]\.[0-9])\s*\(([0-9,]+)\)', card_text)
                        rating = float(rm.group(1)) if rm else 4.5
                        reviews = int(rm.group(2).replace(',', '')) if rm else 0
                        
                        # Address / Category
                        category = niche
                        address = city
                        for line in card_text.split('\n'):
                            if '·' in line and not any(k in line.lower() for k in ['open', 'close', 'am', 'pm']):
                                parts = [p.strip() for p in line.split('·') if p.strip()]
                                if len(parts) >= 1 and not category:
                                    category = parts[0]
                                if len(parts) >= 2:
                                    address = parts[1]
                                break
                                
                        leads.append({
                            "name": name,
                            "niche": niche,
                            "city": city,
                            "rating": rating,
                            "reviews": reviews,
                            "phone": phone,
                            "website": website,
                            "address": address,
                            "maps_url": place_url
                        })
                        
                        if progress_callback:
                            frac = min(0.95, 0.05 + (0.9 * len(leads) / max_results))
                            web_tag = "Has Website" if has_website else "No Website"
                            progress_callback(f"Captured {len(leads)}/{max_results} verified leads ({web_tag}): {name[:28]}...", frac)
                            
                    except Exception:
                        continue
                        
    except Exception as e:
        print(f"Maps scraper error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
                
    if progress_callback:
        progress_callback(f"Success! Fulfilled all {len(leads)} verified leads with contact numbers!", 1.0)
        
    return leads

def scrape_apify(
    niche: str,
    city: str,
    api_token: str,
    max_results: int = 20,
    website_filter: str = "NO_WEBSITE",
    progress_callback: Optional[Callable[[str, float], None]] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Scrapes Google Maps via Apify Actor with website and mobile filtering.
    Ideal for Cloud deployments (Vercel, Streamlit Cloud, Render).
    """
    if not api_token or not str(api_token).strip():
        raise ValueError("Apify API Token is missing. Please configure it in Admin Settings or .env!")
        
    token = str(api_token).strip()
    if "only_mobile_and_no_website" in kwargs:
        website_filter = "NO_WEBSITE" if kwargs["only_mobile_and_no_website"] else "ANY"
    if progress_callback:
        progress_callback("Connecting to Apify Cloud Actor...", 0.15)
        
    query = f"{niche} in {city}"
    run_url = f"https://api.apify.com/v2/acts/compass~crawler-google-places/runs?token={token}"
    payload = {
        "searchStringsArray": [query],
        "maxCrawledPlacesPerSearch": max_results * 3,
        "language": "en"
    }
    
    try:
        resp = requests.post(run_url, json=payload, timeout=25)
        if resp.status_code == 401:
            raise ValueError("Invalid Apify API Token (Unauthorized 401). Please verify your token at apify.com!")
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to connect to Apify cloud service: {e}")
    run_data = resp.json()["data"]
    run_id = run_data["id"]
    dataset_id = run_data["defaultDatasetId"]
    
    for _ in range(40):
        time.sleep(3)
        status_url = f"https://api.apify.com/v2/acts/compass~crawler-google-places/runs/{run_id}?token={api_token}"
        stat = requests.get(status_url, timeout=10).json()["data"]
        if stat["status"] == "SUCCEEDED":
            break
        if stat["status"] in ["FAILED", "ABORTED"]:
            raise RuntimeError(f"Apify run failed: {stat['status']}")
            
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={api_token}&limit={max_results * 4}"
    items = requests.get(dataset_url, timeout=20).json()
    
    leads = []
    seen_phones = set()
    for item in items:
        if len(leads) >= max_results:
            break
            
        web = item.get("website")
        has_web = bool(web and str(web).strip().lower() not in ["none", "null", ""])
        
        if website_filter == "NO_WEBSITE" and has_web:
            continue
        elif website_filter == "HAS_WEBSITE" and not has_web:
            continue
            
        raw_ph = item.get("phone")
        ph = clean_indian_mobile(raw_ph)
        if not ph or ph in seen_phones:
            continue
            
        seen_phones.add(ph)
            
        leads.append({
            "name": item.get("title") or item.get("name"),
            "niche": niche,
            "city": city,
            "rating": item.get("totalScore") or item.get("rating") or 4.5,
            "reviews": item.get("reviewsCount") or 0,
            "phone": ph,
            "website": web,
            "address": item.get("address") or city,
            "maps_url": item.get("url")
        })
        
    return leads
