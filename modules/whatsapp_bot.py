"""
WhatsApp Web Automated Outreach Bot using Selenium.
Allows 1-click sending of both Personalized Message + Uploaded Promotional Poster.
Uses a persistent Chrome profile so the user only logs into WhatsApp Web ONCE.
"""
import os
import time
import urllib.parse
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PROFILE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "whatsapp_chrome_profile")
DEFAULT_POSTER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "agency_poster.png")

def get_whatsapp_driver(headless: bool = False):
    """
    Initializes Chrome driver with persistent WhatsApp Web session profile.
    """
    os.makedirs(PROFILE_DIR, exist_ok=True)
    opts = Options()
    if headless:
        opts.add_argument('--headless=new')
    opts.add_argument(f"user-data-dir={PROFILE_DIR}")
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    return webdriver.Chrome(options=opts)

def open_whatsapp_web_login():
    """
    Opens headed Chrome to web.whatsapp.com so the user can scan QR code once.
    """
    driver = None
    try:
        driver = get_whatsapp_driver(headless=False)
        driver.get("https://web.whatsapp.com")
        # Keep open for 60 seconds to allow QR scan
        time.sleep(45)
    except Exception as e:
        print(f"Error opening WhatsApp Web login: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

def send_whatsapp_automated(phone: str, message: str, image_path: Optional[str] = DEFAULT_POSTER) -> Dict[str, Any]:
    """
    Automates sending message + image poster to a phone number via WhatsApp Web.
    """
    if not phone:
        return {"success": False, "error": "No phone number provided."}
        
    driver = None
    try:
        driver = get_whatsapp_driver(headless=False)
        
        # Navigate to chat
        encoded_text = urllib.parse.quote(message)
        chat_url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_text}"
        driver.get(chat_url)
        
        # Wait up to 25s for chat to load
        time.sleep(10)
        
        # Check if invalid phone popup appeared
        invalid_popups = driver.find_elements(By.XPATH, "//*[contains(text(), 'Phone number shared via url is invalid') or contains(text(), 'phone number is invalid')]")
        if invalid_popups:
            driver.quit()
            return {"success": False, "error": f"WhatsApp reports phone number {phone} is not registered on WhatsApp."}
            
        # Case 1: Send with image poster if file exists
        if image_path and os.path.exists(image_path):
            abs_image_path = os.path.abspath(image_path)
            
            # Locate file input for image/media
            file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            if not file_inputs:
                # Click attach clip button to reveal inputs
                attach_buttons = driver.find_elements(By.CSS_SELECTOR, "span[data-icon='plus'], span[data-icon='attach-menu-plus'], div[title='Attach']")
                if attach_buttons:
                    attach_buttons[0].click()
                    time.sleep(2)
                file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                
            if file_inputs:
                # Send poster image path
                file_inputs[0].send_keys(abs_image_path)
                time.sleep(3)
                
                # In media preview, locate caption or send button
                send_buttons = driver.find_elements(By.CSS_SELECTOR, "span[data-icon='send'], div[aria-label='Send'], span[data-icon='wds-ic-send-filled']")
                if send_buttons:
                    send_buttons[-1].click()
                    time.sleep(5)
                    driver.quit()
                    return {"success": True, "message": f"Poster & Message automatically sent to {phone}!"}
                    
        # Case 2: Send text directly if no poster or file input not found
        text_boxes = driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='10'], div[aria-placeholder*='Type a message']")
        if text_boxes:
            text_boxes[0].send_keys(Keys.ENTER)
            time.sleep(4)
            driver.quit()
            return {"success": True, "message": f"Message sent to {phone} via WhatsApp Web!"}
            
        driver.quit()
        return {"success": False, "error": "Could not locate WhatsApp send button. Please ensure WhatsApp Web is logged in."}
        
    except Exception as e:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        return {"success": False, "error": str(e)}
