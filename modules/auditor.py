"""
Website and Digital Presence Auditor
Audits local businesses & digital marketing agencies for missing websites,
SSL issues, slow load times, mobile friendliness, agency partnerships, and extracts contact emails.
"""
import time
import re
import urllib.parse
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

IGNORE_EMAIL_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.css', '.js')
IGNORE_EMAIL_PATTERNS = ('example.com', 'domain.com', 'email.com', 'yourname@', 'wixpress.com', 'sentry.io', 'cloudflare.com')

def clean_email(email: str) -> Optional[str]:
    email = email.lower().strip().rstrip('.')
    if any(email.endswith(ext) for ext in IGNORE_EMAIL_EXTENSIONS):
        return None
    if any(pat in email for pat in IGNORE_EMAIL_PATTERNS):
        return None
    if len(email) < 6 or len(email) > 60:
        return None
    return email

def extract_emails_from_html(html: str) -> List[str]:
    found_emails = set()
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('mailto:'):
            e = href.replace('mailto:', '').split('?')[0].strip()
            ce = clean_email(e)
            if ce:
                found_emails.add(ce)
                
    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b')
    for match in email_regex.finditer(html):
        ce = clean_email(match.group(0))
        if ce:
            found_emails.add(ce)
            
    return list(found_emails)

def is_agency_niche(niche: str, name: str) -> bool:
    """
    Detects if the business is a Digital Marketing, SEO, Advertising, or Creative Agency.
    """
    text = f"{niche} {name}".lower()
    return any(w in text for w in [
        "marketing", "agency", "advertising", "seo", "digital",
        "creative", "social media", "pr agency", "branding", "media"
    ])

def audit_business(raw_lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes a lead's digital presence and returns audit metrics and lead classification.
    Supports both Local Businesses (No website / bad website) and Agencies / B2B (White-label pitch).
    """
    name = raw_lead.get("name", "Unknown Business")
    niche = raw_lead.get("niche", "")
    website = raw_lead.get("website")
    rating = raw_lead.get("rating") or 0.0
    reviews = raw_lead.get("reviews") or 0
    phone = raw_lead.get("phone") or ""
    
    audit_data = {
        "website_found": False,
        "is_accessible": False,
        "http_status": None,
        "ssl_secure": False,
        "ssl_status": "No Website",
        "load_time_sec": None,
        "mobile_friendly": None,
        "tech_detected": [],
        "has_chat_or_ai": False,
        "emails_found": [],
        "issues": [],
        "pitch_angle": ""
    }
    
    # Check if Digital Marketing Agency or B2B Partner
    is_agency = is_agency_niche(niche, name)
    
    # CASE 1: No Website listed on Google Maps
    if not website or str(website).strip().lower() in ["none", "null", "", "http://none"]:
        audit_data["ssl_status"] = "No Website"
        audit_data["issues"].append("No website URL listed on Google Business Profile.")
        
        if reviews >= 10:
            lead_type = "HOT_NO_WEBSITE"
            score = 95
            audit_data["pitch_angle"] = f"Aapke {reviews}+ reviews hain aur rating {rating}⭐ hai, par online appointment / website nahi hai."
        elif reviews >= 1:
            lead_type = "HOT_NO_WEBSITE"
            score = 85
            audit_data["pitch_angle"] = f"Aapka active business hai ({rating}⭐), par koi modern website nahi hai naye clients attract karne ke liye."
        else:
            lead_type = "HOT_NO_WEBSITE"
            score = 75
            audit_data["pitch_angle"] = "Naya business hai jisko modern website aur Google ranking setup ki sakht zaroorat hai."
            
        return {
            "lead_type": lead_type,
            "audit_score": score,
            "audit_details": audit_data,
            "email": None
        }

    # CASE 2: Website Exists -> Test technical health & agency classification
    audit_data["website_found"] = True
    target_url = website.strip()
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url
        
    start_time = time.time()
    resp = None
    
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        resp = session.get(target_url, timeout=7, allow_redirects=True)
        load_time = round(time.time() - start_time, 2)
        audit_data["load_time_sec"] = load_time
        audit_data["http_status"] = resp.status_code
        audit_data["is_accessible"] = (resp.status_code == 200)
        
        if resp.url.startswith("https://"):
            audit_data["ssl_secure"] = True
            audit_data["ssl_status"] = "Valid HTTPS (Secure)"
        else:
            audit_data["ssl_secure"] = False
            audit_data["ssl_status"] = "Insecure (HTTP Only)"
            audit_data["issues"].append("Website runs on unencrypted HTTP without SSL.")
            
    except requests.exceptions.SSLError:
        audit_data["ssl_secure"] = False
        audit_data["ssl_status"] = "SSL Certificate Expired/Invalid"
        audit_data["issues"].append("Browser shows critical 'SSL Security Warning' to visitors.")
        try:
            resp = requests.get(target_url, timeout=6, verify=False, headers={"User-Agent": USER_AGENT})
            load_time = round(time.time() - start_time, 2)
            audit_data["load_time_sec"] = load_time
            audit_data["http_status"] = resp.status_code
            audit_data["is_accessible"] = True
        except Exception:
            pass
            
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        audit_data["is_accessible"] = False
        audit_data["http_status"] = "Down/Timeout"
        audit_data["ssl_status"] = "Cannot Connect"
        audit_data["issues"].append("Website is DOWN or loading timed out (>7 seconds).")
        
    except Exception as e:
        audit_data["is_accessible"] = False
        audit_data["http_status"] = "Error"
        audit_data["issues"].append(f"Connection error: {str(e)[:50]}")
        
    # Analyze HTML if accessible
    extracted_email = None
    if resp is not None and resp.status_code == 200:
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        
        viewport = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'viewport'})
        audit_data["mobile_friendly"] = "Yes" if viewport else "No"
        if not viewport:
            audit_data["issues"].append("Missing mobile viewport tag. Site not mobile friendly.")
            
        if audit_data["load_time_sec"] and audit_data["load_time_sec"] >= 3.5:
            audit_data["issues"].append(f"Slow page speed ({audit_data['load_time_sec']}s).")
            
        html_lower = html.lower()
        has_chat = any(w in html_lower for w in ["tawk.to", "intercom", "crisp.chat", "tidio", "livechat", "whatsapp-widget", "chat-widget"])
        audit_data["has_chat_or_ai"] = has_chat
        
        emails = extract_emails_from_html(html)
        if not emails and target_url:
            base_url = target_url.rstrip('/')
            for subpath in ['/contact', '/contact-us', '/about']:
                try:
                    sub_resp = requests.get(base_url + subpath, timeout=4, headers={"User-Agent": USER_AGENT})
                    if sub_resp.status_code == 200:
                        sub_emails = extract_emails_from_html(sub_resp.text)
                        if sub_emails:
                            emails.extend(sub_emails)
                            break
                except Exception:
                    pass
        audit_data["emails_found"] = emails
        if emails:
            extracted_email = emails[0]
            
    # Classify Lead Quality
    if is_agency:
        lead_type = "AGENCY_PARTNERSHIP"
        score = 92
        audit_data["pitch_angle"] = "Digital Marketing Agency: Pitch White-Label Web Development & AI WhatsApp Chatbot Partnership."
    elif not audit_data["is_accessible"]:
        lead_type = "HOT_WEBSITE_ISSUES"
        score = 90
        audit_data["pitch_angle"] = "Website load nahi ho rahi ya server down hai."
    elif not audit_data["ssl_secure"]:
        lead_type = "HOT_WEBSITE_ISSUES"
        score = 85
        audit_data["pitch_angle"] = "Website par SSL certificate nahi hai (Shows 'Not Secure')."
    elif audit_data.get("mobile_friendly") == "No":
        lead_type = "HOT_WEBSITE_ISSUES"
        score = 82
        audit_data["pitch_angle"] = "Website mobile devices par responsive nahi hai."
    elif audit_data.get("load_time_sec", 0) >= 3.5:
        lead_type = "HOT_WEBSITE_ISSUES"
        score = 78
        audit_data["pitch_angle"] = f"Website slow hai ({audit_data['load_time_sec']}s)."
    else:
        lead_type = "QUALIFIED_AUTOMATION"
        score = 70
        audit_data["pitch_angle"] = "Website acchi hai: Pitch 24/7 AI WhatsApp Chatbot & Business Automation."
            
    return {
        "lead_type": lead_type,
        "audit_score": score,
        "audit_details": audit_data,
        "email": extracted_email
    }
