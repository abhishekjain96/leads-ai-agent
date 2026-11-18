"""
AI Pitch Generator using Google Gemini API (Free Tier) & Smart Fallback Templates.
Customized for:
Abhishek Jain - Software Developer & Founder of codube.com (Software Development & AI Automation Agency)

Supports:
1. AGENCY_PARTNERSHIP: White-label Tech Development Partner Proposal for Digital Marketing Agencies.
2. HOT_WEBSITE_ISSUES: Revamp & optimization for slow / insecure websites.
3. QUALIFIED_AUTOMATION: 24/7 AI WhatsApp Booking Agent & Lead Capture for good websites.
4. HOT_NO_WEBSITE: Brand new high-converting website & booking system for businesses with no website.
"""
import os
import re
import urllib.parse
from typing import Dict, Any, Optional
from google import genai

def clean_phone_number(raw_phone: str) -> Optional[str]:
    """
    Cleans phone numbers into international WhatsApp format (e.g. 919829012345).
    """
    if not raw_phone:
        return None
    digits = re.sub(r'\D', '', str(raw_phone))
    if not digits:
        return None
    
    # 10 digits starting with 6,7,8,9
    if len(digits) == 10 and digits[0] in '6789':
        return f"91{digits}"
    # 11 digits starting with 0
    if len(digits) == 11 and digits.startswith('0') and digits[1] in '6789':
        return f"91{digits[1:]}"
    # 12 digits starting with 91
    if len(digits) == 12 and digits.startswith('91'):
        return digits
    if len(digits) >= 10:
        return digits
    return None

def is_agency_lead(lead: Dict[str, Any]) -> bool:
    """
    Checks if the lead is a Digital Marketing, SEO, Advertising, or Creative Agency.
    """
    lead_type = lead.get("lead_type", "")
    if lead_type == "AGENCY_PARTNERSHIP":
        return True
    text = f"{lead.get('niche', '')} {lead.get('name', '')}".lower()
    return any(w in text for w in [
        "marketing", "agency", "advertising", "seo", "digital",
        "creative", "social media", "pr agency", "branding", "media"
    ])

def build_fallback_pitches(lead: Dict[str, Any], language: str = "Hinglish") -> Dict[str, str]:
    """
    Clean, high-converting WhatsApp message & Email pitches featuring:
    Abhishek Jain, Software Developer & Founder, codube.com
    Dynamically adapts based on lead type:
    - Agency White-Label Partnership
    - Broken/Slow Website Revamp
    - AI Automation for Good Websites
    - No Website Setup
    """
    name = lead.get("name", "Sir/Madam")
    niche = lead.get("niche") or "business"
    city = lead.get("city") or "local area"
    rating = lead.get("rating") or 4.8
    reviews = lead.get("reviews") or 50
    website = lead.get("website")
    lead_type = lead.get("lead_type") or ("AGENCY_PARTNERSHIP" if is_agency_lead(lead) else "HOT_NO_WEBSITE")
    
    has_website = bool(website and str(website).strip().lower() not in ["none", "null", ""])
    
    # -------------------------------------------------------------
    # CASE 1: DIGITAL MARKETING AGENCY & B2B PARTNERSHIP
    # -------------------------------------------------------------
    if is_agency_lead(lead) or lead_type == "AGENCY_PARTNERSHIP":
        if language == "Hinglish":
            wa_msg = (
                f"Namaste Team {name} Ji! 🙏\n\n"
                f"Maine Google par aapki agency dekhi — aapka marketing work aur market reputation sach me kaafi impressive hai! 🚀\n\n"
                f"Mai *Abhishek Jain*, Software Developer & Founder at *codube.com* (Software Development & AI Automation Agency).\n\n"
                f"Hum top digital marketing aur creative agencies ke saath as a *Dedicated White-Label Tech Partner* collaborate karte hain.\n\n"
                f"Jab aapke clients ko:\n"
                f"✅ Modern Ultra-Fast Websites (Next.js, React, Tailwind, WordPress)\n"
                f"✅ High-Converting Landing Pages & Web Apps\n"
                f"✅ 24/7 AI WhatsApp Chatbots & Booking Automation ki zaroorat hoti hai,\n"
                f"toh hum poori technical development aur delivery handle karte hain — 100% aapke agency brand ke under!\n\n"
                f"💡 *Isse aapka fayda:*\n"
                f"• In-house developers rakhne ka salary aur hiring overhead ZERO\n"
                f"• Aap client se web projects close karke 40%–60% profit margin retain kar sakte hain\n"
                f"• Timely, bug-free delivery with high quality standards.\n\n"
                f"Aap hamara work aur agency portfolio yahan check kar sakte hain: https://codube.com\n\n"
                f"Kya hum is hafte ek quick 5-minute call ya WhatsApp par connect kar sakte hain to explore a win-win partnership? 😊\n\n"
                f"Warm Regards,\n"
                f"*Abhishek Jain*\n"
                f"Software Developer & Founder | codube.com\n"
                f"🌐 https://codube.com"
            )
            email_subj = f"White-Label Web & AI Tech Partner Proposal for {name}"
            email_body = (
                f"Dear {name} Team,\n\n"
                f"I came across your agency while researching leading marketing teams in {city}. Your campaigns and client creative work look exceptional.\n\n"
                f"I am Abhishek Jain, Software Developer and Founder of codube.com (Software Development & AI Automation Agency).\n\n"
                f"We partner with digital marketing, advertising, and SEO agencies as their behind-the-scenes White-Label Tech & Development Team. When your clients need modern responsive websites, custom web apps, Shopify/WordPress development, or 24/7 AI WhatsApp chatbots, we build and deliver everything seamlessly under your agency's brand name.\n\n"
                f"Key Advantages for {name}:\n"
                f"1. No expensive in-house developer salaries or recruitment overhead.\n"
                f"2. You bill your clients at agency rates and retain healthy 40-60% profit margins.\n"
                f"3. Fast turnaround times, clean code, and dedicated technical support.\n\n"
                f"You can review our agency portfolio and recent projects at: https://codube.com\n\n"
                f"Would you be open to a quick 5-minute introductory call or message exchange this week to see how we can support your upcoming client web builds?\n\n"
                f"Best regards,\n"
                f"Abhishek Jain\n"
                f"Software Developer & Founder | codube.com\n"
                f"Website: https://codube.com"
            )
        else: # English
            wa_msg = (
                f"Hello Team {name}! 👋\n\n"
                f"I came across your agency on Google — really impressed by your marketing work and client portfolio! 🚀\n\n"
                f"I am *Abhishek Jain*, Software Developer and Founder of *codube.com* (Software Development & AI Automation Agency).\n\n"
                f"We partner with digital marketing and advertising agencies as their *Dedicated White-Label Tech & Web Development Team*.\n\n"
                f"Whenever your clients need:\n"
                f"✅ High-Speed Responsive Websites (Next.js, React, WordPress)\n"
                f"✅ Custom Web Applications & Landing Pages\n"
                f"✅ 24/7 AI WhatsApp Bots & Business Automation\n"
                f"— we handle the end-to-end technical execution under your agency's brand name.\n\n"
                f"Benefits for {name}:\n"
                f"• Zero overhead of maintaining in-house software engineers\n"
                f"• Keep healthy 40-60% profit margins on web development retainers\n"
                f"• Reliable, pixel-perfect, on-time delivery.\n\n"
                f"Feel free to check our work and portfolio at: https://codube.com\n\n"
                f"Would you be open to a quick 5-minute chat to discuss how we can collaborate? 😊\n\n"
                f"Best regards,\n"
                f"*Abhishek Jain*\n"
                f"Software Developer & Founder | codube.com\n"
                f"🌐 https://codube.com"
            )
            email_subj = f"White-label web & AI tech partner proposal for {name}"
            email_body = (
                f"Dear {name} Team,\n\n"
                f"I came across your agency and was very impressed by your brand presence in {city}.\n\n"
                f"I am Abhishek Jain, Software Developer and Founder of codube.com. We serve as a trusted white-label engineering backend for marketing agencies, delivering custom websites, e-commerce stores, web apps, and AI WhatsApp bots directly under your agency's name.\n\n"
                f"This allows your agency to capture lucrative tech contracts with zero developer payroll overhead.\n\n"
                f"Explore our portfolio at: https://codube.com\n\n"
                f"Could we schedule a quick 5-minute call this week?\n\n"
                f"Sincerely,\n"
                f"Abhishek Jain\n"
                f"Software Developer | codube.com\n"
                f"Website: https://codube.com"
            )
        return {
            "whatsapp": wa_msg.strip(),
            "email_subject": email_subj.strip(),
            "email_body": email_body.strip()
        }

    # -------------------------------------------------------------
    # CASE 2: BUSINESS HAS A WEBSITE WITH ISSUES (SLOW, INSECURE, ETC.)
    # -------------------------------------------------------------
    elif lead_type == "HOT_WEBSITE_ISSUES" or (has_website and lead.get("audit_details", {}).get("issues")):
        issues_list = lead.get("audit_details", {}).get("issues", [])
        issue_desc = issues_list[0] if issues_list else "website speed and mobile responsiveness"
        
        if language == "Hinglish":
            wa_msg = (
                f"Namaste Team {name} Ji! 🙏\n\n"
                f"Maine Google par aapka business dekha — aapke *{reviews}+ positive reviews* aur *{rating}⭐ rating* sach me commendable hain! 👏\n\n"
                f"Maine aapki website ({website}) phone par check ki, aur notice kiya ki: *{issue_desc}*.\n"
                f"Is wajah se lagbhag 40% se 50% visitors page load hone se pehle hi drop ho jaate hain.\n\n"
                f"Mai *Abhishek Jain*, Software Developer at *codube.com* (Software Development & AI Automation Agency). 🚀\n\n"
                f"Hum aapki website ko:\n"
                f"✅ 100% Secure (SSL) aur Ultra-Fast (under 2 seconds load speed)\n"
                f"✅ Modern Mobile-Friendly Design\n"
                f"✅ 24/7 AI WhatsApp Booking Bot se upgrade kar sakte hain jo instant inquiries capture karega.\n\n"
                f"Maine aapke business ke liye ek *Free Preview Redesign Mockup* ready kiya hai.\n"
                f"Kya mai aapko 2-minute ka preview demo link share kar sakta hoon? 😊\n\n"
                f"Warm Regards,\n"
                f"*Abhishek Jain*\n"
                f"Software Developer | codube.com\n"
                f"🌐 https://codube.com"
            )
            email_subj = f"Important website speed & security note for {name}"
            email_body = (
                f"Dear {name} Team,\n\n"
                f"I noticed your impressive {reviews}+ reviews on Google Maps. However, when visiting your website ({website}), I observed: {issue_desc}.\n\n"
                f"This technical friction causes high bounce rates and lost client inquiries.\n\n"
                f"I am Abhishek Jain, Software Developer at codube.com. We help businesses upgrade to high-speed modern websites and automated 24/7 WhatsApp AI booking agents.\n\n"
                f"I've drafted a complimentary revamp mockup for {name}.\n\n"
                f"Would you be open to reviewing a 2-minute demo preview?\n\n"
                f"Best regards,\n"
                f"Abhishek Jain\n"
                f"Software Developer | codube.com\n"
                f"Website: https://codube.com"
            )
        else:
            wa_msg = (
                f"Hello Team {name}! 👋\n\n"
                f"Congratulations on your outstanding *{rating}⭐ rating across {reviews}+ reviews*! 👏\n\n"
                f"I reviewed your website ({website}) and noticed: *{issue_desc}*.\n"
                f"This often results in over 40% of mobile visitors bouncing before taking action.\n\n"
                f"I am *Abhishek Jain*, Software Developer at *codube.com*. We can revamp your site into an ultra-fast, mobile-optimized platform equipped with a 24/7 AI WhatsApp booking assistant.\n\n"
                f"May I share a complimentary 2-minute redesign preview link with you? 😊\n\n"
                f"Best regards,\n"
                f"*Abhishek Jain*\n"
                f"Software Developer | codube.com\n"
                f"🌐 https://codube.com"
            )
            email_subj = f"Website performance & speed improvement for {name}"
            email_body = (
                f"Dear {name} Team,\n\n"
                f"Your Google reviews show great client satisfaction. However, {issue_desc} on your website ({website}) may be impacting conversions.\n\n"
                f"I am Abhishek Jain, Software Developer at codube.com. We specialize in ultra-fast web development and AI lead capture automation.\n\n"
                f"Would you like to review a quick 2-minute preview mockup we created for {name}?\n\n"
                f"Best regards,\n"
                f"Abhishek Jain\n"
                f"Software Developer | codube.com\n"
                f"Website: https://codube.com"
            )
        return {
            "whatsapp": wa_msg.strip(),
            "email_subject": email_subj.strip(),
            "email_body": email_body.strip()
        }

    # -------------------------------------------------------------
    # CASE 3: BUSINESS HAS A GOOD WORKING WEBSITE (PITCH AI AUTOMATION)
    # -------------------------------------------------------------
    elif lead_type == "QUALIFIED_AUTOMATION" or has_website:
        if language == "Hinglish":
            wa_msg = (
                f"Namaste Team {name} Ji! 🙏\n\n"
                f"Maine aapka business aur website ({website}) dekhi — aapka online presence aur {rating}⭐ Google reputation kaafi acchi hai! 👏\n\n"
                f"Lekin aksar 70% visitors website dekh kar bina call ya message kiye chale jaate hain. "
                f"Agar visitors ko website par instant WhatsApp assistant mil jaye jo 24/7 unke sawalon ke jawab de aur appointments book kare, toh leads 2X–3X ho sakti hain!\n\n"
                f"Mai *Abhishek Jain*, Software Developer at *codube.com* (Software Development & AI Automation Agency). 🚀\n\n"
                f"Hum aapki website par ek *Smart 24/7 AI WhatsApp Booking Agent* integrate karte hain jo:\n"
                f"✅ Website visitors ko instantly engage karke unka number aur requirement capture karta hai\n"
                f"✅ Seedha aapke WhatsApp par real hot leads bhejta hai.\n\n"
                f"Maine aapke business ke liye ek live demo taiyar kiya hai. Kya mai 2-minute ka demo link share karoon? 😊\n\n"
                f"Warm Regards,\n"
                f"*Abhishek Jain*\n"
                f"Software Developer | codube.com\n"
                f"🌐 https://codube.com"
            )
            email_subj = f"Adding 24/7 AI Lead & Booking Automation to {name}'s website"
            email_body = (
                f"Dear {name} Team,\n\n"
                f"Your website ({website}) and strong {reviews}+ Google reviews ({rating}⭐) reflect great trust in {city}.\n\n"
                f"Most websites convert only 2-3% of visitors because people want immediate answers on WhatsApp. We help businesses integrate intelligent 24/7 AI WhatsApp Booking Agents that engage visitors in real-time, answer questions, and convert them into booked clients.\n\n"
                f"I am Abhishek Jain, Software Developer at codube.com.\n\n"
                f"Would you be open to a quick 2-minute live demo showing how this AI bot works on your site?\n\n"
                f"Best regards,\n"
                f"Abhishek Jain\n"
                f"Software Developer | codube.com\n"
                f"Website: https://codube.com"
            )
        else:
            wa_msg = (
                f"Hello Team {name}! 👋\n\n"
                f"Your business and website ({website}) have a great reputation on Google! 👏\n\n"
                f"Did you know that over 65% of visitors leave websites without calling? We build *24/7 AI WhatsApp Booking Agents* that automatically capture client inquiries and book appointments directly to your phone.\n\n"
                f"I am *Abhishek Jain*, Software Developer at *codube.com* (https://codube.com).\n\n"
                f"May I share a 2-minute preview demo with you? 😊\n\n"
                f"Best regards,\n"
                f"*Abhishek Jain*\n"
                f"Software Developer | codube.com"
            )
            email_subj = f"24/7 AI Booking Automation for {name}"
            email_body = (
                f"Dear {name} Team,\n\n"
                f"We help high-reputation businesses like {name} turn existing website traffic into booked clients using automated 24/7 AI WhatsApp booking agents.\n\n"
                f"I am Abhishek Jain, Software Developer at codube.com.\n\n"
                f"Would you be open to a 2-minute demo preview?\n\n"
                f"Best regards,\n"
                f"Abhishek Jain\n"
                f"Software Developer | codube.com\n"
                f"Website: https://codube.com"
            )
        return {
            "whatsapp": wa_msg.strip(),
            "email_subject": email_subj.strip(),
            "email_body": email_body.strip()
        }

    # -------------------------------------------------------------
    # CASE 4: BUSINESS HAS NO WEBSITE (HOT_NO_WEBSITE)
    # -------------------------------------------------------------
    else:
        if language == "Hinglish":
            wa_msg = (
                f"Namaste Dr. / Team {name} Ji! 🙏\n\n"
                f"Maine Google Maps par aapka {niche} dekha — aapke *{reviews}+ positive reviews* aur *{rating}⭐ rating* dekh kar kaafi accha laga! "
                f"Market me aapka trust aur reputation sach me top-class hai. 👏\n\n"
                f"Lekin maine notice kiya ki Google Maps par aapki koi *Official Modern Website* ya *Online Appointment Booking* linked nahi hai. "
                f"Aaj kal 70% se zyada clients call karne ki jagah direct online booking ya WhatsApp par instant reply chahte hain.\n\n"
                f"Mai *Abhishek Jain*, Software Developer at *codube.com* (Software Development & AI Automation Agency). 🚀\n\n"
                f"Hum local businesses ke liye:\n"
                f"✅ Modern Ultra-Fast Website (Mobile-Friendly)\n"
                f"✅ 24/7 AI WhatsApp Booking Agent (raat ko bhi inquiries aur appointments handle karta hai)\n"
                f"✅ Google Maps Local SEO Growth setup karte hain.\n\n"
                f"Maine aapke business ke liye ek *Free Preview Demo Layout* design kiya hai jisse aap dekh sakein ki aapki nayi website aur booking system kaisa dikhega.\n\n"
                f"Kya mai aapko 2-minute ka demo preview link share kar sakta hoon? Pasand aaye toh hi baat karenge! 😊\n\n"
                f"Warm Regards,\n"
                f"*Abhishek Jain*\n"
                f"Software Developer | codube.com\n"
                f"🌐 https://codube.com"
            )
            email_subj = f"Quick question regarding {name}'s official website & booking system"
            email_body = (
                f"Dear {name} Team,\n\n"
                f"I came across {name} on Google Maps while researching top-rated {niche}s in {city}. "
                f"Congratulations on your outstanding {reviews}+ positive reviews ({rating}⭐) — your service quality clearly stands out!\n\n"
                f"However, I noticed that you don't currently have an official website or automated booking system linked to your profile. "
                f"Over 65% of potential clients searching locally prefer booking appointments or checking services directly online rather than making phone calls.\n\n"
                f"I am Abhishek Jain, Software Developer at codube.com (Software Development & AI Business Automation Agency).\n\n"
                f"We specialize in:\n"
                f"1. Ultra-fast, responsive modern websites\n"
                f"2. 24/7 WhatsApp AI booking agents that automatically capture client inquiries\n"
                f"3. Local Google ranking optimization\n\n"
                f"I have already drafted a complimentary, custom preview layout specifically designed for {name}.\n\n"
                f"Would you be open to reviewing a 2-minute demo preview? No obligations whatsoever.\n\n"
                f"Best regards,\n"
                f"Abhishek Jain\n"
                f"Software Developer | codube.com\n"
                f"Website: https://codube.com\n"
                f"Agency: codube.com - Software Development & AI Automation"
            )
        else: # English
            wa_msg = (
                f"Hello Team {name}! 👋\n\n"
                f"I discovered your {niche} on Google Maps — huge congratulations on your stellar *{rating}⭐ rating across {reviews}+ reviews*! 👏\n\n"
                f"I noticed your Google profile does not currently have an *Official Website* or online appointment booking linked. "
                f"Nowadays, over 70% of potential clients prefer booking directly online or interacting via instant WhatsApp booking rather than calling.\n\n"
                f"I am *Abhishek Jain*, Software Developer at *codube.com* (Software Development & AI Automation Agency). 🚀\n\n"
                f"We build:\n"
                f"✅ High-Speed Modern Websites (Mobile-Optimized)\n"
                f"✅ 24/7 AI WhatsApp Booking Bots (automating customer appointments)\n"
                f"✅ Google Maps SEO & Review Acceleration\n\n"
                f"I have created a *Free Preview Demo Layout* tailored specifically for {name}.\n\n"
                f"May I share a 2-minute preview link with you? Only if you like it, we can discuss further! 😊\n\n"
                f"Best regards,\n"
                f"*Abhishek Jain*\n"
                f"Software Developer | codube.com\n"
                f"🌐 https://codube.com"
            )
            email_subj = f"Complimentary website & booking mockup for {name}"
            email_body = (
                f"Dear {name} Team,\n\n"
                f"Your impressive {reviews}+ reviews on Google Maps show that clients trust your services. "
                f"However, missing an official website costs local businesses up to 40% of high-intent clients who search online after hours.\n\n"
                f"I am Abhishek Jain, Software Developer at codube.com (Software Development Agency).\n\n"
                f"We help local businesses upgrade into 24/7 automated lead machines with high-speed websites and instant AI booking bots.\n\n"
                f"I've put together a complimentary mockup design for {name}.\n\n"
                f"Would you like to review the 2-minute preview link?\n\n"
                f"Sincerely,\n"
                f"Abhishek Jain\n"
                f"Software Developer | codube.com\n"
                f"Website: https://codube.com"
            )

        return {
            "whatsapp": wa_msg.strip(),
            "email_subject": email_subj.strip(),
            "email_body": email_body.strip()
        }

def generate_pitch(lead: Dict[str, Any], api_key: Optional[str] = None, language: str = "Hinglish") -> Dict[str, str]:
    """
    Generates personalized pitch using Gemini API (if key available) or intelligent templates.
    Always brands as:
    Abhishek Jain, Software Developer & Founder at codube.com (Software Development & AI Automation Agency)
    """
    clean_phone = clean_phone_number(lead.get("phone", ""))
    lead_type = lead.get("lead_type") or ("AGENCY_PARTNERSHIP" if is_agency_lead(lead) else "HOT_NO_WEBSITE")
    is_agency = (lead_type == "AGENCY_PARTNERSHIP" or is_agency_lead(lead))
    
    active_key = api_key or os.getenv("GEMINI_API_KEY")
    pitches = None
    
    if active_key and len(active_key.strip()) > 10:
        try:
            client = genai.Client(api_key=active_key.strip())
            
            if is_agency:
                prompt_task = (
                    "Target: Offer a Dedicated White-Label Web & AI Development Partnership to a Digital Marketing / Advertising Agency.\n"
                    "Core Pitch: They focus on marketing and client acquisition, while Abhishek Jain & codube.com build and deliver all client websites, web apps, landing pages, and AI WhatsApp chatbots 100% white-labeled under the agency's brand on-time with zero in-house developer salary overhead."
                )
            elif lead.get("website"):
                prompt_task = (
                    f"Target: Pitch Website Optimization & 24/7 AI WhatsApp Booking Automation to a business that already has a website ({lead.get('website')}).\n"
                    f"Audit Issues: {lead.get('audit_details', {}).get('issues', ['Needs modern AI lead capture'])}\n"
                    "Core Pitch: Upgrade site speed/security and add 24/7 AI WhatsApp bot to double visitor-to-client conversion."
                )
            else:
                prompt_task = (
                    "Target: Sell a High-Converting Modern Website + 24/7 AI WhatsApp Booking Agent + Business Automation to a local business owner who has good Google ratings but NO website.\n"
                    "Core Pitch: Missing website loses ~40% of clients. Offer free demo preview layout."
                )

            prompt = f"""
You are Abhishek Jain, a professional Software Developer and Founder of 'codube.com' (Software Development & AI Automation Agency).
{prompt_task}

Lead Details:
- Business Name: {lead.get('name')}
- Category/Niche: {lead.get('niche', 'Business')}
- City/Area: {lead.get('city', 'Local')}
- Google Rating: {lead.get('rating')} stars
- Google Reviews: {lead.get('reviews')} reviews
- Phone: {lead.get('phone')}
- Website: {lead.get('website') or 'None'}
- Lead Type: {lead_type}

Sender Profile:
- Name: Abhishek Jain
- Title: Software Developer & Founder
- Agency: codube.com (Software Development & AI Automation Agency)
- Website: https://codube.com

Language: {language} (If Hinglish, write natural, highly respectful, clean professional Hindi in English script with proper spacing, emojis, and WhatsApp bold formatting).

Instructions:
1. WHATSAPP_MESSAGE:
   - Greeting: Polite & respectful
   - Mention their business and reputation warmly.
   - For Agencies: Propose White-Label Tech Partnership (Next.js, React, WordPress, AI bots) under their brand.
   - For Businesses without website: Mention lack of official website and lost online clients.
   - For Businesses with website: Mention speed/conversion improvements and 24/7 AI WhatsApp chatbot.
   - Introduce yourself clearly: "Mai Abhishek Jain, Software Developer at codube.com (Software Development & AI Automation Agency)."
   - Offer a quick low-pressure next step (5-minute chat or free demo).
   - Sign-off:
     Warm Regards,
     *Abhishek Jain*
     Software Developer | codube.com
     🌐 https://codube.com

2. EMAIL_SUBJECT: Curiosity-driven, personalized subject line (max 8 words).
3. EMAIL_BODY: Professional cold email (max 150 words) with clear value proposition and sign-off by Abhishek Jain, codube.com.

Format output EXACTLY:
[WHATSAPP]
(your whatsapp text here)
[/WHATSAPP]
[EMAIL_SUBJECT]
(your email subject here)
[/EMAIL_SUBJECT]
[EMAIL_BODY]
(your email body here)
[/EMAIL_BODY]
"""
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            text = response.text
            
            wa_match = re.search(r'\[WHATSAPP\](.*?)\[/WHATSAPP\]', text, re.DOTALL)
            subj_match = re.search(r'\[EMAIL_SUBJECT\](.*?)\[/EMAIL_SUBJECT\]', text, re.DOTALL)
            body_match = re.search(r'\[EMAIL_BODY\](.*?)\[/EMAIL_BODY\]', text, re.DOTALL)
            
            if wa_match and subj_match and body_match:
                pitches = {
                    "whatsapp": wa_match.group(1).strip(),
                    "email_subject": subj_match.group(1).strip(),
                    "email_body": body_match.group(1).strip()
                }
        except Exception as e:
            print(f"Gemini API warning, falling back to smart template: {e}")
            pitches = None

    if not pitches:
        pitches = build_fallback_pitches(lead, language=language)
        
    wa_url = ""
    if clean_phone:
        encoded_msg = urllib.parse.quote(pitches["whatsapp"])
        wa_url = f"https://wa.me/{clean_phone}?text={encoded_msg}"
        
    return {
        "pitch_whatsapp": pitches["whatsapp"],
        "pitch_whatsapp_url": wa_url,
        "pitch_email_subject": pitches["email_subject"],
        "pitch_email_body": pitches["email_body"]
    }
