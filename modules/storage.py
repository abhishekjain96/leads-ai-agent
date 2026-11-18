"""
Database and Local Storage for Lead Generation Agent (Google Maps & Reddit)
Uses SQLite for zero-config, persistent storage.
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "leads.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Google Maps Leads Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            niche TEXT,
            city TEXT,
            rating REAL,
            reviews INTEGER,
            phone TEXT,
            email TEXT,
            website TEXT,
            address TEXT,
            maps_url TEXT,
            lead_type TEXT, -- HOT_NO_WEBSITE, AGENCY_PARTNERSHIP, HOT_WEBSITE_ISSUES, QUALIFIED_AUTOMATION
            audit_score INTEGER,
            audit_details TEXT,
            pitch_whatsapp TEXT,
            pitch_whatsapp_url TEXT,
            pitch_email_subject TEXT,
            pitch_email_body TEXT,
            outreach_status TEXT DEFAULT 'New',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, phone)
        )
    """)
    
    # 2. Reddit Client Leads Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reddit_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE,
            title TEXT NOT NULL,
            subreddit TEXT,
            author TEXT,
            post_url TEXT,
            selftext TEXT,
            time_ago TEXT,
            lead_intent TEXT,
            ai_confidence INTEGER,
            requirements_summary TEXT,
            pitch_subject TEXT,
            pitch_message TEXT,
            reddit_dm_url TEXT,
            status TEXT DEFAULT 'New',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. System & Admin Settings Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Seed default settings if not exists
    default_settings = {
        "admin_password": "codube@admin",
        "developer_name": "Abhishek Jain",
        "agency_name": "codube.com",
        "portfolio_url": "https://codube.com",
        "contact_whatsapp": "919829012345",
        "default_scraper": "Google Maps Headless Direct (100% Free & Unlimited)"
    }
    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES (?, ?)", (k, v))
        
    conn.commit()
    conn.close()

# ----------------- SYSTEM SETTINGS METHODS -----------------

def get_setting(key: str, default: str = "") -> str:
    """
    Retrieves a setting value from SQLite, falling back to environment variable, then default.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0] is not None and str(row[0]).strip():
        return str(row[0]).strip()
        
    # Fallback to env var (e.g. GEMINI_API_KEY for gemini_api_key)
    env_key = key.upper()
    env_val = os.getenv(env_key) or os.getenv(key)
    if env_val and str(env_val).strip():
        return str(env_val).strip()
        
    return default

def set_setting(key: str, value: str):
    """
    Saves or updates a setting in SQLite.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO system_settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = CURRENT_TIMESTAMP
    """, (key, str(value).strip()))
    conn.commit()
    conn.close()

RELEVANT_SETTING_KEYS = [
    "admin_password", "developer_name", "agency_name", "portfolio_url",
    "contact_whatsapp", "default_scraper", "gemini_api_key", "apify_token",
    "smtp_user", "smtp_pass", "sender_name"
]

def get_all_settings() -> Dict[str, str]:
    """
    Returns all application settings as a key-value dictionary.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM system_settings")
    rows = cursor.fetchall()
    conn.close()
    res = {r[0]: r[1] for r in rows}
    
    # Merge env vars as fallbacks for relevant keys
    for k in RELEVANT_SETTING_KEYS:
        if k not in res or not res[k]:
            env_v = os.getenv(k.upper()) or os.getenv(k)
            if env_v:
                res[k] = env_v
                
    return res

# ----------------- GOOGLE MAPS LEADS METHODS -----------------

def clean_invalid_leads() -> int:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leads WHERE phone IS NULL OR TRIM(phone) = ''")
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def save_lead(lead_dict: Dict[str, Any], website_filter: str = "ANY", **kwargs) -> Optional[int]:
    init_db()
    phone = lead_dict.get("phone")
    website = lead_dict.get("website")
    has_web = bool(website and str(website).strip().lower() not in ["none", "null", ""])
    
    # Handle backward compatibility
    if "require_mobile_and_no_website" in kwargs and kwargs["require_mobile_and_no_website"]:
        website_filter = "NO_WEBSITE"
        
    # Always require valid contact number
    if not phone or len(str(phone).strip()) < 10:
        return None
        
    # Check website filter
    if website_filter == "NO_WEBSITE" and has_web:
        return None
    elif website_filter == "HAS_WEBSITE" and not has_web:
        return None
            
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    audit_str = json.dumps(lead_dict.get("audit_details", {}), ensure_ascii=False)
    
    query = """
        INSERT INTO leads (
            name, niche, city, rating, reviews, phone, email, website,
            address, maps_url, lead_type, audit_score, audit_details,
            pitch_whatsapp, pitch_whatsapp_url, pitch_email_subject, pitch_email_body,
            outreach_status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name, phone) DO UPDATE SET
            rating=excluded.rating,
            reviews=excluded.reviews,
            website=excluded.website,
            lead_type=excluded.lead_type,
            audit_score=excluded.audit_score,
            audit_details=excluded.audit_details,
            pitch_whatsapp=excluded.pitch_whatsapp,
            pitch_whatsapp_url=excluded.pitch_whatsapp_url,
            pitch_email_subject=excluded.pitch_email_subject,
            pitch_email_body=excluded.pitch_email_body
    """
    
    params = (
        lead_dict.get("name"),
        lead_dict.get("niche"),
        lead_dict.get("city"),
        lead_dict.get("rating"),
        lead_dict.get("reviews"),
        phone,
        lead_dict.get("email"),
        website,
        lead_dict.get("address"),
        lead_dict.get("maps_url"),
        lead_dict.get("lead_type", "HOT_NO_WEBSITE"),
        lead_dict.get("audit_score", 0),
        audit_str,
        lead_dict.get("pitch_whatsapp"),
        lead_dict.get("pitch_whatsapp_url"),
        lead_dict.get("pitch_email_subject"),
        lead_dict.get("pitch_email_body"),
        lead_dict.get("outreach_status", "New"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    cursor.execute(query, params)
    conn.commit()
    lead_id = cursor.lastrowid or 1
    conn.close()
    return lead_id

def get_leads(
    lead_type: Optional[str] = None,
    niche: Optional[str] = None,
    city: Optional[str] = None,
    website_filter: str = "All"
) -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM leads WHERE phone IS NOT NULL AND TRIM(phone) != ''"
    params = []
    
    if website_filter == "NO_WEBSITE":
        query += " AND (website IS NULL OR TRIM(website) = '' OR LOWER(website) = 'none')"
    elif website_filter == "HAS_WEBSITE":
        query += " AND website IS NOT NULL AND TRIM(website) != '' AND LOWER(website) != 'none'"
        
    if lead_type and lead_type != "All":
        query += " AND lead_type = ?"
        params.append(lead_type)
        
    if niche and niche != "All":
        query += " AND niche = ?"
        params.append(niche)
        
    if city and city != "All":
        query += " AND city = ?"
        params.append(city)
        
    query += " ORDER BY id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        d = dict(row)
        if d.get("audit_details"):
            try:
                d["audit_details"] = json.loads(d["audit_details"])
            except Exception:
                pass
        results.append(d)
        
    conn.close()
    return results

def update_outreach_status(lead_id: int, status: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET outreach_status = ? WHERE id = ?", (status, lead_id))
    conn.commit()
    conn.close()

def delete_lead(lead_id: int):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()

def clear_all_leads():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leads")
    conn.commit()
    conn.close()

def get_stats() -> Dict[str, int]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE phone IS NOT NULL AND TRIM(phone) != ''")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE (website IS NULL OR TRIM(website) = '' OR LOWER(website) = 'none') AND phone IS NOT NULL AND TRIM(phone) != ''")
    no_website = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE website IS NOT NULL AND TRIM(website) != '' AND LOWER(website) != 'none' AND phone IS NOT NULL AND TRIM(phone) != ''")
    has_website = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE lead_type = 'AGENCY_PARTNERSHIP'")
    agency_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != ''")
    has_email = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE phone IS NOT NULL AND phone != ''")
    has_phone = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE outreach_status != 'New'")
    contacted = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total": total,
        "hot_no_website": no_website,
        "has_website": has_website,
        "agency_partners": agency_count,
        "has_email": has_email,
        "has_phone": has_phone,
        "contacted": contacted
    }

def export_leads_df(leads: List[Dict[str, Any]]) -> pd.DataFrame:
    flat_list = []
    for l in leads:
        audit = l.get("audit_details") or {}
        flat_list.append({
            "ID": l.get("id"),
            "Business Name": l.get("name"),
            "Niche": l.get("niche"),
            "City": l.get("city"),
            "Lead Status": l.get("lead_type"),
            "Rating": l.get("rating"),
            "Reviews": l.get("reviews"),
            "Mobile Number": l.get("phone"),
            "Email": l.get("email"),
            "Website": l.get("website") or "None",
            "Address": l.get("address"),
            "WhatsApp Pitch": l.get("pitch_whatsapp"),
            "WhatsApp Link": l.get("pitch_whatsapp_url"),
            "Email Subject": l.get("pitch_email_subject"),
            "Email Body": l.get("pitch_email_body"),
            "Outreach Status": l.get("outreach_status"),
            "Date Added": l.get("created_at")
        })
    return pd.DataFrame(flat_list)

# ----------------- REDDIT LEADS METHODS -----------------

def save_reddit_lead(lead: Dict[str, Any]) -> Optional[int]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
        INSERT INTO reddit_leads (
            post_id, title, subreddit, author, post_url, selftext,
            time_ago, lead_intent, ai_confidence, requirements_summary,
            pitch_subject, pitch_message, reddit_dm_url, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            time_ago=excluded.time_ago,
            pitch_subject=excluded.pitch_subject,
            pitch_message=excluded.pitch_message,
            reddit_dm_url=excluded.reddit_dm_url
    """
    params = (
        lead.get("post_id"),
        lead.get("title"),
        lead.get("subreddit"),
        lead.get("author"),
        lead.get("post_url"),
        lead.get("selftext"),
        lead.get("time_ago"),
        lead.get("lead_intent", "REAL_CLIENT"),
        lead.get("ai_confidence", 90),
        lead.get("requirements_summary"),
        lead.get("pitch_subject"),
        lead.get("pitch_message"),
        lead.get("reddit_dm_url"),
        lead.get("status", "New"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    cursor.execute(query, params)
    conn.commit()
    lead_id = cursor.lastrowid
    conn.close()
    return lead_id

def get_reddit_leads(status: Optional[str] = None) -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM reddit_leads WHERE 1=1"
    params = []
    if status and status != "All":
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_reddit_lead_status(lead_id: int, status: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE reddit_leads SET status = ? WHERE id = ?", (status, lead_id))
    conn.commit()
    conn.close()

def update_reddit_lead_pitch(lead_id: int, subject: str, message: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT author FROM reddit_leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    author = row[0] if row else ""
    enc_sub = urllib.parse.quote(subject)
    enc_msg = urllib.parse.quote(message)
    dm_url = f"https://www.reddit.com/message/compose/?to={author}&subject={enc_sub}&message={enc_msg}"
    cursor.execute("UPDATE reddit_leads SET pitch_subject = ?, pitch_message = ?, reddit_dm_url = ? WHERE id = ?", (subject, message, dm_url, lead_id))
    conn.commit()
    conn.close()

def delete_reddit_lead(lead_id: int):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reddit_leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()

def clear_all_reddit_leads():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reddit_leads")
    conn.commit()
    conn.close()

def get_reddit_stats() -> Dict[str, int]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM reddit_leads")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM reddit_leads WHERE status = 'New'")
    new_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM reddit_leads WHERE status = 'Approved'")
    approved_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM reddit_leads WHERE status = 'Contacted'")
    contacted_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM reddit_leads WHERE status = 'Rejected'")
    rejected_count = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total": total,
        "new": new_count,
        "approved": approved_count,
        "contacted": contacted_count,
        "rejected": rejected_count
    }
