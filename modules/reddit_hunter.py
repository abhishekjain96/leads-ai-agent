"""
Reddit Real-Time Client Hunter & AI Pitch Engine
Finds recent clients posting "need a website", "hiring developer", etc.
Filters out sellers/spam and generates human, personalized English pitches
from Abhishek Jain | codube.com.
"""
import os
import re
import time
import urllib.parse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from google import genai

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 LeadHunter/2.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
]

DEFAULT_SUBREDDITS = [
    'forhire',
    'freelance_forhire',
    'smallbusiness',
    'Entrepreneur',
    'startups',
    'webdev',
    'HiringCoding',
    'hireaprogrammer'
]

KEYWORD_PRESETS = [
    "need a website",
    "need website",
    "looking for web developer",
    "looking for developer",
    "hiring web developer",
    "build a website",
    "build my website",
    "redesign website",
    "website development",
    "landing page",
    "ecommerce website",
    "business automation",
    "need ai agent"
]

def parse_post_time_ago(updated_iso: str) -> tuple[int, str]:
    """
    Parses ISO timestamp and returns (diff_in_minutes, human_readable_string).
    """
    try:
        now = datetime.now(timezone.utc)
        post_time = datetime.fromisoformat(updated_iso.replace('Z', '+00:00'))
        diff_secs = int((now - post_time).total_seconds())
        diff_mins = max(1, diff_secs // 60)
        
        if diff_mins < 60:
            return diff_mins, f"{diff_mins}m ago"
        hours = diff_mins // 60
        if hours < 24:
            return diff_mins, f"{hours}h {diff_mins % 60}m ago"
        days = hours // 24
        return diff_mins, f"{days}d ago"
    except Exception:
        return 9999, "recent"

DISQUALIFYING_TITLES = [
    r"\banalyst\b", r"\border specialist\b", r"\bprocurement\b", r"\bpeoplesoft\b",
    r"\bservicenow\b", r"\bnetwork engineer\b", r"\bot network\b", r"\bvideo edit(ing|or)?\b",
    r"\baudio\b", r"\bvoiceover\b", r"\baccountant\b", r"\baccounting\b", r"\bbookkeeper\b",
    r"\bvirtual assistant\b", r"\bdata entry\b", r"\btranscription\b", r"\bcopywriter\b",
    r"\bcontent writer\b", r"\bartwork\b", r"\billustrator\b", r"\b3d\b", r"\bcad\b",
    r"\btax\b", r"\bfinance\b", r"\bsupply chain\b", r"\bwarehouse\b", r"\breceptionist\b"
]

TARGET_WEB_REGEX = [
    r"\bwebsite\b",
    r"\bweb developer\b",
    r"\bweb design(er)?\b",
    r"\bweb development\b",
    r"\blanding page\b",
    r"\bweb app(lication)?\b",
    r"\bfrontend\b",
    r"\bfront-end\b",
    r"\bbackend\b",
    r"\bback-end\b",
    r"\bfullstack\b",
    r"\bfull-stack\b",
    r"\bsoftware developer\b",
    r"\bcustom software\b",
    r"\bwordpress\b",
    r"\bshopify\b",
    r"\bnext\.?js\b",
    r"\breact(\.?js)?\b",
    r"\bvue(\.?js)?\b",
    r"\bbooking system\b",
    r"\bai agent\b",
    r"\bwhatsapp bot\b",
    r"\bbusiness automation\b"
]

def is_seller_or_spam(title: str, text: str) -> bool:
    """
    Detects if post is from a seller/freelancer offering services instead of a client hiring.
    """
    tl = title.lower()
    b = text.lower()
    
    # In forhire/freelance_forhire, [For Hire] means SELLER!
    if "[for hire]" in tl or "(for hire)" in tl or "for hire" in tl or "[available]" in tl:
        return True
    if "i am offering" in b or "hire me" in b or "services i provide" in b or "my services" in b:
        return True
    if "portfolio:" in b and ("[hiring]" not in tl and "hiring" not in tl):
        return True
    if "available for work" in tl or "available for hire" in tl or "open for work" in tl:
        return True
    if tl.startswith("i will build") or tl.startswith("i will design") or tl.startswith("offering"):
        return True
    return False

def matches_target_criteria(title: str, text: str, keywords: List[str]) -> bool:
    """
    Strictly checks if post is a genuine client inquiry for website/software development.
    Disqualifies unrelated roles (finance, network engineer, CAD, video editing).
    """
    title_lower = title.lower()
    body_lower = text.lower()
    full_content = f"{title_lower} {body_lower}"
    
    # 1. Check title disqualifiers (e.g. Analyst Order Specialist, Network Engineer, CAD)
    for disq in DISQUALIFYING_TITLES:
        if re.search(disq, title_lower):
            return False
            
    # 2. Must match web/software target regex
    has_web_match = any(re.search(pat, full_content) for pat in TARGET_WEB_REGEX)
    
    # 3. If [Hiring] is in title, ensure it matches a real web/software development requirement
    if "[hiring]" in title_lower or "hiring" in title_lower:
        if has_web_match:
            return True
            
    # 4. Check explicit client search keywords (e.g. "need a website", "looking for developer")
    for kw in keywords:
        kw_clean = kw.lower().strip()
        if kw_clean in full_content:
            return True
            
    return False

def generate_reddit_pitch(
    post_title: str,
    post_body: str,
    author: str,
    subreddit: str,
    api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Generates natural human English pitch tailored to the Reddit post.
    Features Abhishek Jain, Software Developer & Founder of codube.com.
    """
    clean_author = author.replace("/u/", "").strip()
    
    # Default high-converting human pitch template
    fallback_subject = f"Regarding your project in r/{subreddit} - Web & Software Developer"
    fallback_message = (
        f"Hi {clean_author},\n\n"
        f"I came across your post in r/{subreddit} regarding your website/software project. "
        f"I'm Abhishek Jain, a Software Developer and founder of codube.com (Software Development & AI Automation Agency).\n\n"
        f"I specialize in building high-speed, modern websites, custom web applications, and automated booking systems with clean code and high conversion rates.\n\n"
        f"You can check out our work and portfolio at: https://codube.com\n\n"
        f"I'd love to understand your exact vision and share a few relevant live examples of what we've built. "
        f"Would you be open to a quick 5-minute chat or exchanging a few messages here on Reddit?\n\n"
        f"Best regards,\n"
        f"Abhishek Jain\n"
        f"Software Developer | codube.com\n"
        f"Website: https://codube.com"
    )
    
    ai_summary = "Client needs website development or custom software."
    ai_intent = "REAL_CLIENT"
    ai_confidence = 90
    
    active_key = api_key or os.getenv("GEMINI_API_KEY")
    if active_key and len(active_key.strip()) > 10:
        try:
            client = genai.Client(api_key=active_key.strip())
            prompt = f"""
You are Abhishek Jain, a professional Software Developer and Founder of 'codube.com' (Software Development & AI Business Automation Agency).
You are responding to a potential client's post on Reddit.

Reddit Post Details:
- Subreddit: r/{subreddit}
- Author: u/{clean_author}
- Post Title: {post_title}
- Post Content: {post_body[:1000]}

Sender Profile:
- Name: Abhishek Jain
- Role: Software Developer
- Agency: codube.com (Software Development & AI Automation Agency)
- Portfolio: https://codube.com

Instructions:
1. Verify if this post is a REAL CLIENT looking to hire/build a website or app (REAL_CLIENT) or if it's spam/another seller (SELLER_SPAM).
2. If REAL_CLIENT, write a warm, natural, highly personal human English direct message (max 120 words).
   - Do NOT sound like an automated robotic copy-paste template.
   - Mention the specific requirement or challenge they posted about.
   - Mention that you are Abhishek Jain from codube.com (https://codube.com).
   - Propose a low-pressure next step (e.g. sharing relevant work samples or a 5-minute chat).
3. Generate a clean subject line (max 6 words).
4. Summarize their project requirements in 1 sentence.

Format output EXACTLY:
[INTENT]
REAL_CLIENT or SELLER_SPAM
[/INTENT]
[SUMMARY]
(1 sentence summary of what client needs)
[/SUMMARY]
[SUBJECT]
(subject line here)
[/SUBJECT]
[MESSAGE]
(personalized reddit message here)
[/MESSAGE]
"""
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            text = response.text
            
            int_m = re.search(r'\[INTENT\](.*?)\[/INTENT\]', text, re.DOTALL)
            sum_m = re.search(r'\[SUMMARY\](.*?)\[/SUMMARY\]', text, re.DOTALL)
            sub_m = re.search(r'\[SUBJECT\](.*?)\[/SUBJECT\]', text, re.DOTALL)
            msg_m = re.search(r'\[MESSAGE\](.*?)\[/MESSAGE\]', text, re.DOTALL)
            
            if int_m and sub_m and msg_m:
                ai_intent = int_m.group(1).strip()
                ai_summary = sum_m.group(1).strip() if sum_m else ai_summary
                fallback_subject = sub_m.group(1).strip()
                fallback_message = msg_m.group(1).strip()
                ai_confidence = 95 if "REAL" in ai_intent else 40
        except Exception as e:
            print(f"Gemini Reddit pitch warning: {e}")

    # Build Reddit Compose Direct Message URL
    enc_sub = urllib.parse.quote(fallback_subject)
    enc_msg = urllib.parse.quote(fallback_message)
    reddit_dm_url = f"https://www.reddit.com/message/compose/?to={clean_author}&subject={enc_sub}&message={enc_msg}"
    
    return {
        "intent": ai_intent,
        "summary": ai_summary,
        "confidence": ai_confidence,
        "subject": fallback_subject,
        "message": fallback_message,
        "reddit_dm_url": reddit_dm_url
    }

def hunt_reddit_leads(
    subreddits: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    max_age_minutes: int = 1440, # default 24h, can be set to 15, 30, 60
    max_results: int = 15,
    api_key: Optional[str] = None,
    reddit_client_id: Optional[str] = None,
    reddit_client_secret: Optional[str] = None,
    progress_callback: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Main Reddit Hunter engine.
    Scrapes subreddits via RSS or PRAW, filters for real buyer clients,
    evaluates freshness, and generates human pitches.
    """
    target_subs = subreddits if subreddits else DEFAULT_SUBREDDITS
    target_keywords = keywords if keywords else KEYWORD_PRESETS
    
    leads = []
    seen_ids = set()
    
    if progress_callback:
        progress_callback("Connecting to Reddit live streams...", 0.1)
        
    session = requests.Session()
    
    for sub_idx, sub in enumerate(target_subs):
        if len(leads) >= max_results:
            break
            
        if progress_callback:
            frac = 0.1 + (0.7 * (sub_idx / len(target_subs)))
            progress_callback(f"Scanning r/{sub} for recent client posts (Found {len(leads)}/{max_results})...", frac)
            
        url = f"https://www.reddit.com/r/{sub}/new/.rss"
        user_agent = USER_AGENTS[sub_idx % len(USER_AGENTS)]
        
        try:
            time.sleep(1.2) # Polite interval
            r = session.get(url, headers={'User-Agent': user_agent}, timeout=8)
            if r.status_code != 200:
                continue
                
            root = ET.fromstring(r.text)
            entries = root.findall('{http://www.w3.org/2005/Atom}entry')
            
            for entry in entries:
                if len(leads) >= max_results:
                    break
                    
                post_id_elem = entry.find('{http://www.w3.org/2005/Atom}id')
                post_id = post_id_elem.text if post_id_elem is not None else ""
                if not post_id or post_id in seen_ids:
                    continue
                seen_ids.add(post_id)
                
                title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                
                author_elem = entry.find('{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name')
                author = author_elem.text if author_elem is not None else ""
                clean_author = author.replace('/u/', '').strip()
                
                # Filter out bot or deleted authors
                if not clean_author or clean_author.lower() in ['automoderator', '[deleted]', 'reddit']:
                    continue
                    
                link_elem = entry.find('{http://www.w3.org/2005/Atom}link')
                post_url = link_elem.get('href') if link_elem is not None else ""
                
                updated_elem = entry.find('{http://www.w3.org/2005/Atom}updated')
                updated_iso = updated_elem.text if updated_elem is not None else ""
                diff_mins, time_ago_str = parse_post_time_ago(updated_iso)
                
                # Freshness check
                if diff_mins > max_age_minutes:
                    continue
                    
                # Body content
                content_elem = entry.find('{http://www.w3.org/2005/Atom}content')
                body_text = ""
                if content_elem is not None and content_elem.text:
                    soup = BeautifulSoup(content_elem.text, 'html.parser')
                    body_text = soup.get_text().strip()
                    
                # 1. Anti-spam filter: reject sellers
                if is_seller_or_spam(title, body_text):
                    continue
                    
                # 2. Topic filter: matches website / development / hiring
                if not matches_target_criteria(title, body_text, target_keywords):
                    continue
                    
                # 3. AI Pitch & Qualification
                pitch_info = generate_reddit_pitch(
                    post_title=title,
                    post_body=body_text,
                    author=clean_author,
                    subreddit=sub,
                    api_key=api_key
                )
                
                # If AI strictly marked it as SELLER_SPAM, skip
                if pitch_info.get("intent") == "SELLER_SPAM":
                    continue
                    
                leads.append({
                    "post_id": post_id,
                    "title": title,
                    "subreddit": f"r/{sub}",
                    "author": clean_author,
                    "post_url": post_url,
                    "selftext": body_text[:600],
                    "time_ago": time_ago_str,
                    "diff_mins": diff_mins,
                    "lead_intent": pitch_info.get("intent", "REAL_CLIENT"),
                    "ai_confidence": pitch_info.get("confidence", 90),
                    "requirements_summary": pitch_info.get("summary", ""),
                    "pitch_subject": pitch_info.get("subject", ""),
                    "pitch_message": pitch_info.get("message", ""),
                    "reddit_dm_url": pitch_info.get("reddit_dm_url", ""),
                    "status": "New"
                })
                
        except Exception as e:
            print(f"Error scraping r/{sub}: {e}")
            continue

    if progress_callback:
        progress_callback(f"Successfully harvested {len(leads)} genuine client leads from Reddit!", 1.0)
        
    return leads
