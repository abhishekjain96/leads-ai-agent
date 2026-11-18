import os
import time
import urllib.parse
from PIL import Image
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Load local environment if present
load_dotenv()

from modules.storage import (
    init_db, save_lead, get_leads, get_stats,
    update_outreach_status, delete_lead, clear_all_leads,
    clean_invalid_leads, export_leads_df,
    save_reddit_lead, get_reddit_leads, update_reddit_lead_status,
    update_reddit_lead_pitch, delete_reddit_lead, clear_all_reddit_leads,
    get_reddit_stats, get_setting, set_setting, get_all_settings
)
from modules.scraper import scrape_google_maps_direct, scrape_apify, is_chrome_available
from modules.auditor import audit_business
from modules.ai_pitcher import generate_pitch, clean_phone_number
from modules.email_sender import test_smtp_connection, send_cold_email
from modules.whatsapp_bot import send_whatsapp_automated, open_whatsapp_web_login
from modules.reddit_hunter import hunt_reddit_leads, DEFAULT_SUBREDDITS, KEYWORD_PRESETS

# Initialize SQLite database
init_db()

POSTER_PATH = os.path.join(os.path.dirname(__file__), "data", "agency_poster.png")

# Safe rerun helper for compatibility across Streamlit versions
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

# Page configuration
st.set_page_config(
    page_title="Leads AI Agent | Abhishek Jain - codube.com",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern enterprise styling
st.markdown("""
<style>
    .showcase-banner {
        background: linear-gradient(135deg, #091322 0%, #0f2744 50%, #0284c7 100%);
        border: 1px solid #1e3a5f;
        border-radius: 14px;
        padding: 22px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    .badge-demo {
        background-color: #10B981;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        display: inline-block;
        margin-bottom: 8px;
    }
    .badge-admin {
        background-color: #F59E0B;
        color: black;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 800;
        display: inline-block;
        margin-bottom: 8px;
    }
    .showcase-title {
        color: #ffffff;
        font-size: 1.85rem;
        font-weight: 800;
        margin: 4px 0 8px 0;
    }
    .showcase-subtitle {
        color: #cbd5e1;
        font-size: 0.98rem;
        margin: 0;
        line-height: 1.5;
    }
    .badge-reddit {
        background-color: #FF4500;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .badge-client {
        background-color: #10B981;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .badge-agency {
        background-color: #6366F1;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE & SETTINGS -----------------
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False
if "latest_hunt_leads" not in st.session_state:
    st.session_state["latest_hunt_leads"] = []
if "custom_gemini_key" not in st.session_state:
    st.session_state["custom_gemini_key"] = ""
if "custom_apify_token" not in st.session_state:
    st.session_state["custom_apify_token"] = ""

# Load Master System Settings
sys_settings = get_all_settings()
admin_pass = sys_settings.get("admin_password", "codube@admin")
master_gemini_key = sys_settings.get("gemini_api_key", os.getenv("GEMINI_API_KEY", ""))
master_apify_token = sys_settings.get("apify_token", os.getenv("APIFY_TOKEN", ""))
master_smtp_user = sys_settings.get("smtp_user", os.getenv("SMTP_USER", ""))
master_smtp_pass = sys_settings.get("smtp_pass", os.getenv("SMTP_PASS", ""))
master_sender_name = sys_settings.get("sender_name", os.getenv("SENDER_NAME", "Abhishek Jain | codube.com"))
dev_name = sys_settings.get("developer_name", "Abhishek Jain")
agency_name = sys_settings.get("agency_name", "codube.com")
agency_brand = agency_name
portfolio_url = sys_settings.get("portfolio_url", "https://codube.com")
contact_whatsapp = sys_settings.get("contact_whatsapp", "919829012345")

# Resolved Active Credentials
active_gemini_key = st.session_state["custom_gemini_key"] if st.session_state["custom_gemini_key"] else master_gemini_key
active_apify_token = st.session_state["custom_apify_token"] if st.session_state["custom_apify_token"] else master_apify_token
active_smtp_user = master_smtp_user
active_smtp_pass = master_smtp_pass
active_sender_name = master_sender_name

has_active_gemini = bool(active_gemini_key and len(active_gemini_key.strip()) > 8)
has_active_apify = bool(active_apify_token and len(active_apify_token.strip()) > 6)
chrome_is_ready = is_chrome_available()

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
    st.markdown(f"### **{agency_name}**")
    st.markdown(f"**{dev_name}** | Software Developer & Founder")
    st.caption("Software Development & AI Automation Agency")
    st.markdown("---")
    
    # Language Pitch Selector
    language_choice = st.selectbox(
        "Outreach Pitch Tone",
        ["Hinglish", "English"],
        help="Hinglish is ideal for Indian local businesses & agencies. English is recommended for international outreach."
    )
    
    st.markdown("---")

    # =========================================================================
    # VIEW A: ADMIN LOGGED IN
    # =========================================================================
    if st.session_state["is_admin"]:
        st.success("👑 **Admin Mode Active**", icon="🛡️")
        st.caption("Settings configured here apply system-wide for all visitors & clients.")
        
        with st.expander("🔑 Master AI & Cloud Keys", expanded=True):
            new_gemini = st.text_input(
                "Master Gemini API Key",
                value=master_gemini_key,
                type="password",
                help="Free tier from aistudio.google.com. Powers client demo mode so visitors don't have to enter their own key."
            )
            new_apify = st.text_input(
                "Master Apify Token ('apper')",
                value=master_apify_token,
                type="password",
                help="From apify.com. Cloud-based scraper Actor (compass/crawler-google-places). Works on Vercel/Cloud without Chrome!"
            )
            if st.button("💾 Save Master Keys", key="save_admin_keys", type="primary", use_container_width=True):
                set_setting("gemini_api_key", new_gemini)
                set_setting("apify_token", new_apify)
                st.success("Master keys saved to SQLite!")
                time.sleep(1)
                safe_rerun()

        with st.expander("📧 Cold Email (Gmail SMTP)", expanded=False):
            new_smtp_user = st.text_input("Sender Gmail", value=master_smtp_user, placeholder="youremail@gmail.com")
            new_smtp_pass = st.text_input("Gmail App Password", value=master_smtp_pass, type="password", help="16-character Google App Password")
            new_sender = st.text_input("Sender Display Name", value=master_sender_name)
            
            c_adm_em1, c_adm_em2 = st.columns(2)
            with c_adm_em1:
                if st.button("💾 Save SMTP", key="save_admin_smtp", use_container_width=True):
                    set_setting("smtp_user", new_smtp_user)
                    set_setting("smtp_pass", new_smtp_pass)
                    set_setting("sender_name", new_sender)
                    st.success("SMTP Saved!")
                    time.sleep(1)
                    safe_rerun()
            with c_adm_em2:
                if st.button("🧪 Test SMTP", key="test_admin_smtp", use_container_width=True):
                    res = test_smtp_connection(new_smtp_user, new_smtp_pass)
                    if res["success"]:
                        st.success("SMTP OK!")
                    else:
                        st.error(res["error"])

        with st.expander("🏢 Agency Branding & Profile", expanded=False):
            new_dev = st.text_input("Developer Name", value=dev_name)
            new_agency = st.text_input("Agency Name", value=agency_name)
            new_url = st.text_input("Portfolio URL", value=portfolio_url)
            new_wa = st.text_input("Contact WhatsApp", value=contact_whatsapp, help="International format e.g. 919829012345")
            if st.button("💾 Save Profile", key="save_admin_profile", use_container_width=True):
                set_setting("developer_name", new_dev)
                set_setting("agency_name", new_agency)
                set_setting("portfolio_url", new_url)
                set_setting("contact_whatsapp", new_wa)
                st.success("Profile Saved!")
                time.sleep(1)
                safe_rerun()

        with st.expander("📸 Agency Promotional Poster", expanded=False):
            uploaded_file = st.file_uploader("Upload Flyer/Poster (PNG/JPG)", type=["png", "jpg", "jpeg"])
            if uploaded_file is not None:
                with open(POSTER_PATH, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Poster updated successfully!")
            if os.path.exists(POSTER_PATH):
                st.image(POSTER_PATH, caption="Active Outreach Poster", use_column_width=True)

        with st.expander("⚙️ Admin Password & Database Cleanup", expanded=False):
            new_pass = st.text_input("Change Admin Password", value=admin_pass, type="password")
            if st.button("Update Password"):
                set_setting("admin_password", new_pass)
                st.success("Password updated!")
                
            st.markdown("---")
            if st.button("🧹 Clean Invalid Leads (No Phone)", use_container_width=True):
                del_count = clean_invalid_leads()
                st.info(f"Purged {del_count} invalid records.")
                safe_rerun()
                
            if st.button("⚠️ Clear Entire Leads Database", use_container_width=True):
                clear_all_leads()
                clear_all_reddit_leads()
                st.warning("Database reset.")
                safe_rerun()

        if st.button("🚪 Logout from Admin Portal", use_container_width=True):
            st.session_state["is_admin"] = False
            safe_rerun()

    # =========================================================================
    # VIEW B: PUBLIC CLIENT DEMO MODE
    # =========================================================================
    else:
        st.markdown("**🟢 Client Demo System Status**")
        if has_active_gemini:
            st.success("✨ **AI Pitch Engine:** Online (Pre-configured)")
        else:
            st.info("💡 **AI Pitch Engine:** Smart Template Mode Active")
            
        if has_active_apify:
            st.success("☁️ **Cloud Scraper (Apify):** Ready")
        elif chrome_is_ready:
            st.success("🖥️ **Direct Maps Scraper:** Ready")
        else:
            st.warning("⚠️ Scraper Engine: Configure Apify in Admin Settings")

        st.caption("You can test lead generation, digital auditing, and personalized proposals right away!")

        # Optional Custom Keys for Visitor
        with st.expander("🔑 Advanced: Use Your Own API Key (Optional)"):
            c_key = st.text_input("Custom Gemini API Key", value=st.session_state["custom_gemini_key"], type="password")
            c_tok = st.text_input("Custom Apify Token", value=st.session_state["custom_apify_token"], type="password")
            if st.button("Apply Custom Keys for this Session"):
                st.session_state["custom_gemini_key"] = c_key
                st.session_state["custom_apify_token"] = c_tok
                st.success("Session keys applied!")
                safe_rerun()

        # Admin Login
        with st.expander("🔒 Admin Portal (Agency Owner)"):
            login_pass = st.text_input("Admin Passcode", type="password", key="admin_login_input")
            if st.button("Login as Admin", key="btn_admin_login", use_container_width=True):
                if login_pass.strip() == admin_pass.strip():
                    st.session_state["is_admin"] = True
                    st.success("Welcome Abhishek! Loading Admin Panel...")
                    time.sleep(1)
                    safe_rerun()
                else:
                    st.error("Incorrect passcode. (Default: codube@admin)")

# ----------------- MAIN VIEW HEADER -----------------
wa_chat_url = f"https://wa.me/{contact_whatsapp}?text=Hi%20{urllib.parse.quote(dev_name)}%2C%20I%20just%20tested%20your%20Leads%20AI%20Agent%20demo%20on%20{agency_name}%20and%20would%20like%20to%20discuss%20a%20project%21"

st.markdown(f"""
<div class="showcase-banner">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <span class="{'badge-admin' if st.session_state['is_admin'] else 'badge-demo'}">
                {'👑 Admin Mode: Managing System' if st.session_state['is_admin'] else '● Public Client Demo Mode'}
            </span>
            <div class="showcase-title">🎯 Autonomous Leads AI Agent</div>
            <p class="showcase-subtitle">
                Engineered for <b>{dev_name}</b> (Software Developer & Founder at <b>{agency_name}</b>)<br>
                Multi-Channel Local Business & Agency Lead Hunter • Technical Website Auditor • 1-Click WhatsApp & Cold Email Outreach Engine
            </p>
        </div>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <a href="{wa_chat_url}" target="_blank" style="text-decoration: none;">
                <button style="background-color: #25D366; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 0.95rem;">
                    💬 Chat with {dev_name.split()[0]}
                </button>
            </a>
            <a href="{portfolio_url}" target="_blank" style="text-decoration: none;">
                <button style="background-color: #0284c7; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 0.95rem;">
                    🌐 Visit {agency_name}
                </button>
            </a>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Top Channel Selector
channel_mode = st.radio(
    "Choose Lead Generation Channel:",
    [
        "📍 Google Maps Local Businesses & Marketing Agencies",
        "🔴 Reddit Real-Time Clients (People Posting 'Need a Website' or Hiring)"
    ],
    horizontal=True
)

st.markdown("---")

# =========================================================================
# CHANNEL 1: GOOGLE MAPS LEADS
# =========================================================================
if "Google Maps" in channel_mode:
    # KPI Metrics
    stats = get_stats()
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Target Leads (Mobile Ready)", stats["total"])
    col2.metric("🤝 Agency Partners", stats.get("agency_partners", 0), help="Digital Marketing Agencies for White-Label Tech Partnership")
    col3.metric("🔥 No Website (Hot)", stats["hot_no_website"], help="Highest conversion potential")
    col4.metric("🌐 Has Website", stats.get("has_website", 0), help="Websites with issues or for AI automation")
    col5.metric("🚀 Contacted", stats["contacted"])

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Lead Hunter (Google Maps)",
        "🔥 Hot Leads & 1-Click Outreach Hub",
        "📊 CRM Table & CSV Export",
        "📘 Free Setup & Sales Guide"
    ])

    # --- TAB 1: LEAD HUNTER ---
    with tab1:
        st.subheader("Search Real Local Businesses from Google Maps")
        st.info("🎯 **Target-Driven Continuous Hunting:** Whatever number of leads you specify, the agent will hunt across sub-areas until it gathers the **EXACT target amount** of verified leads with mobile numbers matching your target strategy!", icon="🔥")
        
        col_niche, col_city, col_count = st.columns([2, 2, 1])
        
        popular_niches = [
            "Digital Marketing Agencies",
            "SEO & Advertising Agencies",
            "Dental Clinics",
            "Dermatologist & Skin Clinics",
            "Salons & Spas",
            "Gyms & Fitness Centers",
            "Real Estate Agencies",
            "Cafes & Fine Dining Restaurants",
            "Lawyers & Advocates",
            "Physiotherapy Centers",
            "Chartered Accountants",
            "Car Detailing & Garages",
            "Custom..."
        ]
        
        with col_niche:
            niche_select = st.selectbox("Business Category / Niche", popular_niches)
            if niche_select == "Custom...":
                target_niche = st.text_input("Enter custom niche", placeholder="e.g. Pet Care Clinics")
            else:
                target_niche = niche_select
                
        with col_city:
            target_city = st.text_input("Target City / Area", value="Jaipur, Malviya Nagar", placeholder="e.g. Jaipur, Malviya Nagar or Delhi")
            
        with col_count:
            max_leads = st.number_input("Target Leads to Acquire", min_value=3, max_value=150, value=10, step=5)

        is_agency_search = ("Marketing" in target_niche or "Agency" in target_niche or "SEO" in target_niche or "Advertising" in target_niche)

        c_filt1, c_filt2 = st.columns([3, 2])
        with c_filt1:
            target_strategy = st.radio(
                "Lead Acquisition Target Strategy:",
                [
                    "🎯 Businesses WITH Website (e.g. Digital Marketing Agencies, B2B — White-Label Proposal)",
                    "🔥 Businesses WITHOUT Website (e.g. Clinics, Salons, Gyms — New Website + AI Bot Pitch)",
                    "🌐 Both (All Leads with Verified Phone & Contact Number)"
                ],
                index=0 if is_agency_search else 1,
                help="Choose whether to target agencies/companies that already have a website, or local businesses without one."
            )
            if "WITH Website" in target_strategy:
                selected_web_filter = "HAS_WEBSITE"
            elif "WITHOUT Website" in target_strategy:
                selected_web_filter = "NO_WEBSITE"
            else:
                selected_web_filter = "ANY"

        with c_filt2:
            # Build intelligent scraper choices
            scraper_options = []
            if has_active_apify:
                scraper_options.append("Apify Cloud Scraper (Cloud-Safe, Zero Setup)")
            if chrome_is_ready:
                scraper_options.append("Google Maps Headless Direct (100% Free & Unlimited)")
            if not scraper_options:
                scraper_options = ["Google Maps Headless Direct (100% Free & Unlimited)", "Apify Cloud Scraper (Requires Apify Token)"]
                
            scraper_mode = st.radio(
                "Scraper Engine",
                scraper_options,
                index=0,
                help="Apify is 100% cloud-safe (runs on Apify servers). Headless Direct runs Chrome locally."
            )

        if st.button("🚀 Start Lead Hunter Agent", type="primary", use_container_width=True):
            if not target_niche or not target_city:
                st.error("Please enter both Business Niche and Target City/Area.")
            else:
                progress_bar = st.progress(0.0)
                status_text = st.empty()
                
                def update_progress(msg, frac):
                    status_text.info(msg)
                    progress_bar.progress(frac)
                    
                with st.spinner(f"Agent hunting {max_leads} verified leads across Google Maps..."):
                    raw_leads = []
                    try:
                        if "Apify" in scraper_mode:
                            if not active_apify_token:
                                st.error("Apify Token missing. Please add your Apify token in the Admin Settings or .env file!")
                            else:
                                raw_leads = scrape_apify(
                                    target_niche, target_city, active_apify_token, max_leads,
                                    website_filter=selected_web_filter, progress_callback=update_progress
                                )
                        else:
                            raw_leads = scrape_google_maps_direct(
                                target_niche, target_city, max_leads,
                                website_filter=selected_web_filter, progress_callback=update_progress
                            )
                    except Exception as e:
                        st.error(f"Scraper error: {e}")
                        
                    st.write(f"Scraped **{len(raw_leads)}** qualified businesses with valid contact numbers! Now auditing and generating proposals...")
                    
                    saved_count = 0
                    current_hunt = []
                    for idx, raw in enumerate(raw_leads):
                        frac = 0.6 + (0.4 * (idx + 1) / max(len(raw_leads), 1))
                        status_text.text(f"Auditing & pitching {idx+1}/{len(raw_leads)}: {raw.get('name')}")
                        progress_bar.progress(frac)
                        
                        audit_res = audit_business(raw)
                        combined = {**raw, **audit_res}
                        
                        pitches = generate_pitch(combined, api_key=active_gemini_key, language=language_choice)
                        final_lead = {**combined, **pitches}
                        
                        lid = save_lead(final_lead, website_filter=selected_web_filter)
                        if lid is not None:
                            saved_count += 1
                            final_lead["id"] = lid
                            current_hunt.append(final_lead)
                            
                    st.session_state["latest_hunt_leads"] = current_hunt
                    progress_bar.progress(1.0)
                    status_text.empty()
                    
                    if saved_count > 0:
                        st.success(f"🎉 Complete! Captured and saved all {saved_count} verified leads with contact numbers and custom pitches!")
                        st.balloons()
                    else:
                        st.warning("⚠️ No leads matched your exact strategy in this area. Try selecting 'Both (All Leads)' or broadening your city search!")

        # --- LIVE HUNT PREVIEW SECTION (Instant feedback for clients testing the app) ---
        if st.session_state["latest_hunt_leads"]:
            st.markdown("---")
            st.markdown("### ⚡ **Latest Hunt Results (Instant Review & 1-Click Outreach)**")
            st.caption(f"Showing {len(st.session_state['latest_hunt_leads'])} fresh leads from your latest hunt:")
            
            for lh in st.session_state["latest_hunt_leads"]:
                lh_name = lh["name"]
                lh_phone = lh.get("phone", "")
                lh_web = lh.get("website") or "None"
                lh_type = lh.get("lead_type", "HOT_NO_WEBSITE")
                lh_wa_url = lh.get("pitch_whatsapp_url", "")
                lh_wa_msg = lh.get("pitch_whatsapp", "")
                
                badge_color = "#6366F1" if lh_type == "AGENCY_PARTNERSHIP" else ("#10B981" if lh_type == "HOT_NO_WEBSITE" else "#F59E0B")
                tag_label = "🤝 AGENCY WHITE-LABEL" if lh_type == "AGENCY_PARTNERSHIP" else ("🔥 NO WEBSITE" if lh_type == "HOT_NO_WEBSITE" else "⚠️ SITE ISSUES")
                
                with st.container():
                    st.markdown(f"""
                    <div style="border: 1px solid #334155; border-radius: 10px; padding: 14px 18px; margin-bottom: 12px; background-color: #0b1320;">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                            <div>
                                <span style="background-color: {badge_color}; color: white; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700;">{tag_label}</span>
                                <h4 style="margin: 6px 0 2px 0; color: #ffffff;">{lh_name}</h4>
                                <p style="margin: 0; color: #94a3b8; font-size: 0.85rem;">📞 Mobile: <b>{lh_phone}</b> &nbsp;|&nbsp; 🌐 Website: {lh_web}</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_lh1, c_lh2 = st.columns([3, 1])
                    with c_lh1:
                        st.caption(f"**Proposal Preview:** {lh_wa_msg[:160]}...")
                    with c_lh2:
                        if lh_wa_url:
                            st.markdown(
                                f'''<a href="{lh_wa_url}" target="_blank" style="text-decoration: none;">
                                    <button style="background-color: #25D366; color: white; border: none; padding: 8px 12px; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%;">
                                        🟢 Open in WhatsApp
                                    </button>
                                </a>''',
                                unsafe_allow_html=True
                            )

    # --- TAB 2: HOT LEADS & CRM ---
    with tab2:
        st.subheader("🔥 Verified Leads & Outreach Hub (Mobile Ready)")
        
        col_filter1, col_filter2, col_search = st.columns([2, 2, 3])
        with col_filter1:
            type_filter = st.selectbox(
                "Filter Category",
                ["All", "AGENCY_PARTNERSHIP", "HOT_NO_WEBSITE", "HOT_WEBSITE_ISSUES", "QUALIFIED_AUTOMATION"],
                format_func=lambda x: {
                    "All": "🌐 All Target Leads",
                    "AGENCY_PARTNERSHIP": "🤝 Digital Marketing Agencies (White-Label Tech Partner)",
                    "HOT_NO_WEBSITE": "🔥 Hot Leads: No Website",
                    "HOT_WEBSITE_ISSUES": "⚠️ Leads: Broken/Slow Website",
                    "QUALIFIED_AUTOMATION": "⚡ Leads: Good Website (AI Automation)"
                }.get(x, x)
            )
        with col_filter2:
            outreach_filter = st.selectbox(
                "Outreach Status",
                ["All", "New", "WhatsApp Sent", "Email Sent", "Converted", "Dismissed"]
            )
        with col_search:
            search_query = st.text_input("Search Business or Mobile", placeholder="Type name or phone...")

        leads = get_leads(lead_type=type_filter if type_filter != "All" else None)
        
        if outreach_filter != "All":
            leads = [l for l in leads if l.get("outreach_status") == outreach_filter]
        if search_query:
            sq = search_query.lower()
            leads = [l for l in leads if sq in l.get("name", "").lower() or sq in (l.get("phone") or "")]

        if not leads:
            st.info("No leads found matching current filters. Go to Tab 1 to run a Google Maps search!")
        else:
            st.write(f"Showing **{len(leads)}** hot leads with mobile numbers:")
            
            for lead in leads:
                lid = lead["id"]
                lname = lead["name"]
                lphone = lead.get("phone") or ""
                lemail = lead.get("email") or ""
                lweb = lead.get("website") or "None"
                lrating = lead.get("rating") or 0.0
                lreviews = lead.get("reviews") or 0
                ltype = lead.get("lead_type", "HOT_NO_WEBSITE")
                lstatus = lead.get("outreach_status", "New")
                
                if ltype == "AGENCY_PARTNERSHIP":
                    badge = "🤝 AGENCY WHITE-LABEL PARTNER"
                elif ltype == "HOT_NO_WEBSITE":
                    badge = "🔥 NO WEBSITE"
                elif ltype == "HOT_WEBSITE_ISSUES":
                    badge = "⚠️ WEBPAGE ISSUES"
                else:
                    badge = "⚡ AI AUTOMATION READY"

                with st.expander(f"{lname}  |  ⭐ {lrating} ({lreviews} reviews)  |  📱 {lphone}  |  {badge}  |  [{lstatus}]", expanded=(lstatus == "New")):
                    col_left, col_right = st.columns([1, 1])
                    
                    with col_left:
                        st.markdown("**Business Info:**")
                        st.markdown(f"• **Niche:** {lead.get('niche')} in {lead.get('city')}")
                        st.markdown(f"• **Address:** {lead.get('address') or 'N/A'}")
                        st.markdown(f"• **Verified Mobile:** `{lphone}`")
                        st.markdown(f"• **Website:** {f'[{lweb}]({lweb})' if lweb not in ['None', None, ''] else '❌ No Official Website Listed'}")
                        if lead.get("maps_url"):
                            st.markdown(f"• **Google Maps:** [View on Maps]({lead.get('maps_url')})")
                            
                        st.markdown("---")
                        if ltype == "AGENCY_PARTNERSHIP":
                            st.markdown("• **Lead Strategy:** Digital Marketing Agency — High-value client for **White-Label Tech & Development Outsourcing**.")
                            st.markdown(f"• Agency sells websites, web apps, and bots to their clients; **{agency_brand}** executes development behind the scenes.")
                        elif ltype == "HOT_NO_WEBSITE":
                            st.markdown(f"• Business has **{lreviews}+ reviews** ({lrating}⭐) with budget.")
                            st.markdown("• Missing website means losing ~40% of potential online clients.")
                        else:
                            st.markdown(f"• Business has an active website ({lweb}).")
                            st.markdown("• Pitch website performance overhaul & 24/7 AI WhatsApp bot automation.")
                        
                        if os.path.exists(POSTER_PATH):
                            st.image(POSTER_PATH, caption="Promotional Poster (Auto-attached on send)", width=260)
                            
                    with col_right:
                        st.markdown(f"**Personalized Outreach Pitch ({agency_brand} / {dev_name}):**")
                        wa_tab, email_tab = st.tabs(["💬 WhatsApp Outreach", "📧 Cold Email"])
                        
                        with wa_tab:
                            wa_pitch = lead.get("pitch_whatsapp") or ""
                            st.text_area("Clean WhatsApp Message", value=wa_pitch, height=220, key=f"wa_txt_{lid}")
                            wa_url = lead.get("pitch_whatsapp_url")
                            
                            c_wa1, c_wa2, c_wa3 = st.columns([2, 2, 1])
                            with c_wa1:
                                if wa_url:
                                    st.markdown(
                                        f'''<a href="{wa_url}" target="_blank" style="text-decoration: none;">
                                            <button style="background-color: #25D366; color: white; border: none; padding: 10px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%;">
                                                🟢 Open in WhatsApp (1-Click)
                                            </button>
                                        </a>''',
                                        unsafe_allow_html=True
                                    )
                            with c_wa2:
                                if st.button("⚡ Auto-Send Web Bot", key=f"btn_wa_auto_{lid}"):
                                    with st.spinner("Automating WhatsApp Web sending..."):
                                        res = send_whatsapp_automated(lphone, wa_pitch, POSTER_PATH)
                                        if res["success"]:
                                            st.success(res["message"])
                                            update_outreach_status(lid, "WhatsApp Sent")
                                            safe_rerun()
                                        else:
                                            st.error(res["error"])
                            with c_wa3:
                                if st.button("Done", key=f"btn_wa_mark_{lid}"):
                                    update_outreach_status(lid, "WhatsApp Sent")
                                    st.success("Marked!")
                                    safe_rerun()

                        with email_tab:
                            email_subj = lead.get("pitch_email_subject") or ""
                            email_body = lead.get("pitch_email_body") or ""
                            target_email = st.text_input("Recipient Email", value=lemail, key=f"em_to_{lid}")
                            new_subj = st.text_input("Subject", value=email_subj, key=f"em_sub_{lid}")
                            new_body = st.text_area("Body", value=email_body, height=160, key=f"em_bdy_{lid}")
                            
                            c_em1, c_em2 = st.columns([2, 1])
                            with c_em1:
                                if st.button("📤 Send Email (With Poster Attached)", key=f"btn_send_em_{lid}", type="primary"):
                                    if not active_smtp_user or not active_smtp_pass:
                                        st.error("Configure Gmail SMTP in Admin Settings first!")
                                    elif not target_email:
                                        st.error("Please enter email.")
                                    else:
                                        res = send_cold_email(target_email, new_subj, new_body, active_smtp_user, active_smtp_pass, active_sender_name, POSTER_PATH)
                                        if res["success"]:
                                            st.success(res["message"])
                                            update_outreach_status(lid, "Email Sent")
                                            safe_rerun()
                                        else:
                                            st.error(res["error"])
                            with c_em2:
                                if st.button("Mark Emailed", key=f"btn_em_done_{lid}"):
                                    update_outreach_status(lid, "Email Sent")
                                    st.success("Updated!")
                                    safe_rerun()

                    c_st1, c_st2, c_st3 = st.columns([2, 2, 1])
                    with c_st1:
                        status_options = ["New", "WhatsApp Sent", "Email Sent", "Converted", "Dismissed"]
                        curr_idx = status_options.index(lstatus) if lstatus in status_options else 0
                        new_st = st.selectbox("CRM Status", status_options, index=curr_idx, key=f"sel_st_{lid}")
                        if new_st != lstatus:
                            update_outreach_status(lid, new_st)
                            safe_rerun()
                    with c_st3:
                        if st.button("🗑️ Delete", key=f"del_{lid}"):
                            delete_lead(lid)
                            st.warning("Deleted.")
                            safe_rerun()

    # --- TAB 3: TABLE & EXPORT ---
    with tab3:
        st.subheader("📊 Export Leads to CSV / Excel")
        all_leads = get_leads()
        if not all_leads:
            st.info("No leads in database yet.")
        else:
            df = export_leads_df(all_leads)
            st.dataframe(df, use_container_width=True)
            col_exp1, col_exp2, col_clear = st.columns([1, 1, 2])
            with col_exp1:
                st.download_button("📥 Download CSV", data=df.to_csv(index=False).encode('utf-8'), file_name="hot_leads_codube.csv", mime="text/csv", type="primary", use_container_width=True)
            with col_exp2:
                import io
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Hot Leads")
                st.download_button("📗 Download Excel", data=excel_buffer.getvalue(), file_name="hot_leads_codube.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with col_clear:
                if st.button("⚠️ Clear All Maps Leads"):
                    clear_all_leads()
                    safe_rerun()

    # --- TAB 4: SETUP GUIDE ---
    with tab4:
        st.subheader(f"📘 Setup & Sales Closing Guide for {dev_name} ({agency_brand})")
        st.markdown(f"""
        ### 🎯 Strategy 1: Partnering with Digital Marketing Agencies (B2B Retainers)
        **Target:** Marketing Agencies, SEO Firms, Social Media & Advertising Agencies (who have websites and contact numbers).
        - **Why Agencies are the Highest-ROI Target:**
          Digital marketing agencies already have dozens of paying clients who constantly need new websites, landing pages, Shopify stores, and WhatsApp booking bots. But most agencies do NOT have full-time developers due to high salary costs.
        - **Your Proposition as {dev_name} ({agency_brand}):**
          Offer to be their **Dedicated White-Label Tech Partner**. You build and maintain everything under their agency name.
        - **Financial Opportunity:**
          One marketing agency can give you 2-4 website projects every single month (₹50,000 – ₹1,50,000/month recurring pipeline).

        ---
        ### 🎯 Strategy 2: Local Businesses with NO Website (Direct Client Acquisition)
        **Target:** Dental clinics, Salons, Gyms, Dermatologists with 50+ Google reviews and no website.
        - **Step 1:** Click **🟢 Open in WhatsApp (1-Click)** to review the pre-written, highly respectful message.
        - **Step 2:** The message compliments their rating, highlights lost online booking revenue, and offers a **Free Preview Demo** from **{agency_brand}**.
        - **Step 3:** When they reply, share a 2-minute mockup layout. When they love the look, close the package (Website + 24/7 AI WhatsApp bot: ₹15,000 – ₹35,000).

        ---
        ### 🎯 Strategy 3: Reddit Real-Time Client Hunter (High-Ticket USD)
        **Target:** International founders & business owners posting "Need a Website" on Reddit.
        - Monitor subreddits like `r/forhire`, `r/smallbusiness`, `r/Entrepreneur`.
        - Reach out within **15-60 minutes** using the **💬 1-Click Send Reddit DM** button before competitors flood their inbox.
        """)

# =========================================================================
# CHANNEL 2: REDDIT REAL-TIME CLIENT HUNTER
# =========================================================================
else:
    r_stats = get_reddit_stats()
    c_r1, c_r2, c_r3, c_r4 = st.columns(4)
    c_r1.metric("Total Reddit Leads", r_stats["total"])
    c_r2.metric("🔥 New Client Requests", r_stats["new"])
    c_r3.metric("✅ Approved", r_stats["approved"])
    c_r4.metric("💬 Contacted / DMed", r_stats["contacted"])

    r_tab1, r_tab2, r_tab3 = st.tabs([
        "🔍 Reddit Client Scanner (Live)",
        "🔥 Review & 1-Click Outreach Hub (Approved / Edit / Reject)",
        "📘 How Reddit Client Acquisition Works"
    ])

    # --- REDDIT TAB 1: SCANNER ---
    with r_tab1:
        st.subheader("Scan Live Reddit for Clients Posting 'Need a Website' or Hiring Developers")
        st.caption("Extracts real-time posts, uses AI to filter out sellers/spam, and crafts human English direct pitches.")
        
        col_r_time, col_r_res = st.columns([2, 1])
        with col_r_time:
            time_filter = st.selectbox(
                "Freshness Filter (Post Age)",
                [
                    ("⚡ Ultra-Fresh: Last 15 to 60 Minutes (Hot Intent)", 60),
                    ("🕒 Last 3 Hours", 180),
                    ("📅 Last 12 Hours", 720),
                    ("🗓️ Last 24 Hours", 1440)
                ],
                format_func=lambda x: x[0]
            )
            max_age_mins = time_filter[1]
        with col_r_res:
            max_r_leads = st.number_input("Max Client Posts to Gather", min_value=5, max_value=50, value=15, step=5)
            
        col_r_sub, col_r_kw = st.columns([1, 1])
        with col_r_sub:
            selected_subs = st.multiselect(
                "Subreddits to Monitor",
                DEFAULT_SUBREDDITS,
                default=['forhire', 'freelance_forhire', 'smallbusiness', 'Entrepreneur', 'startups']
            )
            custom_sub = st.text_input("Add Custom Subreddit (Optional)", placeholder="e.g. ecommerce")
            if custom_sub:
                selected_subs.append(custom_sub.replace("r/", "").strip())
                
        with col_r_kw:
            selected_kws = st.multiselect(
                "Target Keywords (Client Intent)",
                KEYWORD_PRESETS,
                default=["need a website", "looking for web developer", "hiring web developer", "build a website", "landing page", "business automation"]
            )
            custom_kw = st.text_input("Add Custom Keyword (Optional)", placeholder="e.g. shopify store")
            if custom_kw:
                selected_kws.append(custom_kw.strip())

        st.markdown("---")
        if st.button("🚀 Hunt Live Reddit Clients Now", type="primary", use_container_width=True):
            r_prog = st.progress(0.0)
            r_status = st.empty()
            
            def update_r_prog(msg, frac):
                r_status.info(msg)
                r_prog.progress(frac)
                
            with st.spinner("Monitoring Reddit streams, filtering fake/seller posts with AI, and crafting pitches..."):
                leads = hunt_reddit_leads(
                    subreddits=selected_subs,
                    keywords=selected_kws,
                    max_age_minutes=max_age_mins,
                    max_results=max_r_leads,
                    api_key=active_gemini_key,
                    progress_callback=update_r_prog
                )
                
                saved_r_count = 0
                for l in leads:
                    lid = save_reddit_lead(l)
                    if lid:
                        saved_r_count += 1
                        
                r_prog.progress(1.0)
                r_status.empty()
                if saved_r_count > 0:
                    st.success(f"🎉 Found {saved_r_count} genuine client posts! Go to the 'Review & 1-Click Outreach Hub' tab to send DMs.")
                    st.balloons()
                else:
                    st.warning("No new hiring posts found within that exact time limit. Try broadening the Freshness filter to 'Last 12 Hours' or adding more subreddits!")
                time.sleep(1)
                safe_rerun()

    # --- REDDIT TAB 2: REVIEW & OUTREACH HUB ---
    with r_tab2:
        st.subheader("🔥 Reddit Client Review & 1-Click DM Dispatcher")
        st.caption("Approve, Edit, Reject, or Message clients directly on Reddit with 1 click!")
        
        c_rf1, c_rf2 = st.columns([1, 2])
        with c_rf1:
            r_status_filter = st.selectbox("Filter Status", ["All", "New", "Approved", "Contacted", "Rejected"])
        with c_rf2:
            r_search = st.text_input("Search Title or Author", placeholder="Type username or keyword...")
            
        r_leads = get_reddit_leads(status=r_status_filter if r_status_filter != "All" else None)
        
        if r_search:
            rs = r_search.lower()
            r_leads = [l for l in r_leads if rs in l.get("title", "").lower() or rs in l.get("author", "").lower()]
            
        if not r_leads:
            st.info("No Reddit leads in database matching this filter. Click 'Hunt Live Reddit Clients Now' in Tab 1!")
        else:
            st.write(f"Showing **{len(r_leads)}** client leads:")
            
            for rl in r_leads:
                rl_id = rl["id"]
                rl_title = rl["title"]
                rl_sub = rl.get("subreddit") or "r/reddit"
                rl_author = rl.get("author") or "user"
                rl_time = rl.get("time_ago") or "recent"
                rl_intent = rl.get("lead_intent") or "REAL_CLIENT"
                rl_summary = rl.get("requirements_summary") or "Website/Software project"
                rl_status = rl.get("status", "New")
                rl_url = rl.get("post_url") or "#"
                rl_text = rl.get("selftext") or ""
                rl_dm_url = rl.get("reddit_dm_url") or ""
                
                exp_label = f"[{rl_sub}] {rl_title[:75]}...  |  u/{rl_author}  |  🔥 {rl_time}  |  [{rl_status}]"
                
                with st.expander(exp_label, expanded=(rl_status in ["New", "Approved"])):
                    col_r_post, col_r_pitch = st.columns([1, 1])
                    
                    with col_r_post:
                        st.markdown(f"**Reddit Post Details:**")
                        st.markdown(f"• **Subreddit:** `{rl_sub}`")
                        st.markdown(f"• **Author:** `u/{rl_author}`  [View Profile](https://www.reddit.com/user/{rl_author})")
                        st.markdown(f"• **Posted:** `{rl_time}`")
                        st.markdown(f"• **AI Intent Analysis:** <span class='badge-client'>✅ {rl_intent}</span>", unsafe_allow_html=True)
                        st.markdown(f"• **Summary:** *{rl_summary}*")
                        st.markdown(f"• **Live Post:** [🔗 Open Original Reddit Post]({rl_url})")
                        st.markdown("---")
                        st.markdown("**Client Post Text:**")
                        st.info(rl_text if rl_text else rl_title)
                        
                    with col_r_pitch:
                        st.markdown(f"**Personalized Human English Pitch ({dev_name} | {agency_brand}):**")
                        
                        curr_subj = st.text_input("Subject", value=rl.get("pitch_subject", ""), key=f"r_sub_{rl_id}")
                        curr_msg = st.text_area("Message Body (Direct & Human)", value=rl.get("pitch_message", ""), height=180, key=f"r_msg_{rl_id}")
                        
                        # Action Buttons
                        c_act1, c_act2, c_act3 = st.columns([2, 1, 1])
                        
                        with c_act1:
                            # Re-encode DM url in case user edited text
                            enc_s = urllib.parse.quote(curr_subj)
                            enc_m = urllib.parse.quote(curr_msg)
                            fresh_dm_url = f"https://www.reddit.com/message/compose/?to={rl_author}&subject={enc_s}&message={enc_m}"
                            
                            st.markdown(
                                f'''<a href="{fresh_dm_url}" target="_blank" style="text-decoration: none;">
                                    <button style="background-color: #FF4500; color: white; border: none; padding: 10px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%;">
                                        💬 1-Click Send Reddit DM
                                    </button>
                                </a>''',
                                unsafe_allow_html=True
                            )
                        with c_act2:
                            if st.button("Mark Sent", key=f"btn_r_sent_{rl_id}"):
                                update_reddit_lead_status(rl_id, "Contacted")
                                st.success("Marked as Contacted!")
                                safe_rerun()
                        with c_act3:
                            if st.button("Save Edit", key=f"btn_r_save_{rl_id}"):
                                update_reddit_lead_pitch(rl_id, curr_subj, curr_msg)
                                st.success("Saved!")
                                safe_rerun()
                                
                    st.markdown("---")
                    # Review Decision Bar: Approve / Reject / Delete
                    c_dec1, c_dec2, c_dec3, c_dec4 = st.columns([2, 2, 2, 1])
                    with c_dec1:
                        if st.button("✅ Approve Lead", key=f"appr_{rl_id}", use_container_width=True):
                            update_reddit_lead_status(rl_id, "Approved")
                            st.success("Lead Approved!")
                            safe_rerun()
                    with c_dec2:
                        if st.button("❌ Reject (Not a Client)", key=f"rej_{rl_id}", use_container_width=True):
                            update_reddit_lead_status(rl_id, "Rejected")
                            st.warning("Lead marked as Rejected.")
                            safe_rerun()
                    with c_dec4:
                        if st.button("🗑️", key=f"del_r_{rl_id}"):
                            delete_reddit_lead(rl_id)
                            safe_rerun()

    # --- REDDIT TAB 3: GUIDE ---
    with r_tab3:
        st.subheader(f"📘 How Reddit Client Acquisition Works for {agency_brand}")
        st.markdown(f"""
        ### 🎯 Why Reddit is a Goldmine for High-Ticket Web & Software Clients:
        Every single hour, dozens of founders, business owners, and startup creators post on Reddit:
        - *"Need someone to build a clean landing page for my new venture"*
        - *"Looking for a reliable web developer to revamp our website"*
        - *"Need custom business automation & booking system"*

        ### ⚡ The 15-Minute Advantage:
        When a client posts on `r/forhire` or `r/smallbusiness`, they get 20+ generic bot responses within 2 hours.
        **The secret to closing deals is SPEED and HUMAN TOUCH**:
        1. Our agent detects posts within **15 to 60 minutes**.
        2. Gemini crafts a **natural, human message** addressing their exact problem.
        3. You click **"💬 1-Click Send Reddit DM"** — Reddit opens with their username and your pitch already typed!
        4. You are the **first real human agency founder ({dev_name} | {agency_brand})** in their inbox!
        5. Conversion rate is over **25-40%** because you reached out before competitors.
        """)
