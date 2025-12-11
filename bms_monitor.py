import streamlit as st
import time
import random
import sys
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.parse

# Try to import curl_cffi for browser impersonation (fixes 403 errors)
try:
    from curl_cffi import requests
    USING_CURL_CFFI = True
except ImportError:
    import requests
    USING_CURL_CFFI = False

# --- CONFIGURATION & CONSTANTS ---
PAGE_TITLE = "🏏 T20 Ticket Monitor"
PAGE_ICON = "🎟️"

# Keywords
SUCCESS_KEYWORDS = ["Login to book", "Book Now", "Select Seats", "Buy Tickets"]
WAIT_KEYWORDS = ["Coming Soon", "Notify Me", "Interested", "Not Available"]

# User Agents for fallback
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]

# --- FUNCTIONS ---

def send_telegram_alert(token, chat_id, message):
    """Sends a message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        # Use standard requests for API calls (curl_cffi not needed here)
        if USING_CURL_CFFI:
            import requests as std_requests
            std_requests.post(url, json=payload, timeout=10)
        else:
            requests.post(url, json=payload, timeout=10)
        return True
    except Exception as e:
        st.error(f"Telegram Error: {e}")
        return False

def send_whatsapp_alert(phone, api_key, message):
    """Sends a message via CallMeBot (Free WhatsApp Gateway)."""
    encoded_msg = urllib.parse.quote(message)
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_msg}&apikey={api_key}"
    
    try:
        if USING_CURL_CFFI:
            import requests as std_requests
            std_requests.get(url, timeout=10)
        else:
            requests.get(url, timeout=10)
        return True
    except Exception as e:
        st.error(f"WhatsApp Error: {e}")
        return False

def check_status(target_url):
    """Checks the BMS page status."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'https://in.bookmyshow.com/',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        if USING_CURL_CFFI:
            response = requests.get(target_url, impersonate="chrome", headers=headers, timeout=15)
        else:
            response = requests.get(target_url, headers=headers, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()

            # Logic
            found_success = any(keyword in text for keyword in SUCCESS_KEYWORDS)
            
            if found_success:
                return True, f"[{timestamp}] SUCCESS: Booking keywords found!"
            
            # Anti-False Positive: If page is too small, it might be a captcha/block
            if len(text) < 500:
                return False, f"[{timestamp}] WARNING: Page content too short (Blocked?). Retrying..."

            return False, f"[{timestamp}] Status: Still waiting... (Coming Soon detected)"
        
        elif response.status_code == 403:
            return False, f"[{timestamp}] Blocked (403). Retrying..."
        else:
            return False, f"[{timestamp}] Error: HTTP {response.status_code}"

    except Exception as e:
        return False, f"[{timestamp}] Error: {str(e)}"

# --- STREAMLIT UI ---

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON)

st.title(f"{PAGE_ICON} {PAGE_TITLE}")
st.markdown("Monitor **BookMyShow** for ticket availability and get instant alerts.")

# Sidebar - Settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    target_url = st.text_input("Event URL", value="https://in.bookmyshow.com/sports/canada-vs-united-arab-emirates-icc-men-s-t20-wc-2026/ET00474012")
    # target_url = st.text_input("Event URL", value="https://in.bookmyshow.com/sports/india-vs-namibia-icc-men-s-t20-wc-2026/ET00474011")
    check_interval = st.number_input("Check Interval (seconds)", min_value=30, value=60)
    
    st.divider()
    st.subheader("📢 Notifications")
    
    # Default to Telegram
    notify_method = st.radio("Notification Method", ["Telegram", "WhatsApp (CallMeBot)", "None"], index=0)
    
    tg_token = ""
    tg_chat_id = ""
    wa_phone = ""
    wa_key = ""
    
    if notify_method == "Telegram": # Option A
        st.info("**Option A: Telegram (Recommended & Most Reliable)**")
        with st.expander("Click here for setup instructions"):
            st.markdown("""
            1.  Open Telegram and search for **`@BotFather`**.
            2.  Send the message: `/newbot`.
            3.  Follow the steps (name your bot). It will give you a **Token** (e.g., `123456:ABC-DEF1234...`). **Copy this.**
            4.  Now search for **`@userinfobot`** on Telegram and click Start. It will reply with your **Id** (e.g., `12345678`). **Copy this.**
            5.  Enter these two values below.
            """)
        tg_token = st.text_input("Bot Token", value="8432333925:AAEL2c3H-A9v7zYcGQVeH0oNnaD9ICBWj3U", type="password", help="From @BotFather")
        tg_chat_id = st.text_input("Chat ID", value="5812598196", help="From @userinfobot")
        if st.button("Test Telegram"):
            send_telegram_alert(tg_token, tg_chat_id, "Test Alert from BMS Monitor!")
            st.success("Test sent!")

    elif notify_method == "WhatsApp (CallMeBot)": # Option B
        st.info("**Option B: WhatsApp (via CallMeBot)**")
        with st.expander("Click here for setup instructions"):
            st.markdown("""
            1.  Save this number in your phone contacts: `+34 621 331 709` (Name it "CallMeBot").
            2.  Send this exact message to that contact on WhatsApp: `I allow callmebot to send me messages`
            3.  Wait 10-20 seconds. It will reply with your **API Key**.
            4.  Enter your phone number (e.g., `+919999999999`) and this API Key below.
            """)
        wa_phone = st.text_input("Phone Number (with country code)", placeholder="+919876543210")
        wa_key = st.text_input("API Key", type="password", help="Get from https://www.callmebot.com/blog/free-api-whatsapp-messages/")
        if st.button("Test WhatsApp"):
            send_whatsapp_alert(wa_phone, wa_key, "Test Alert from BMS Monitor!")
            st.success("Test sent!")

# Main Control
col1, col2 = st.columns(2)
with col1:
    start_btn = st.button("▶️ Start Monitoring", type="primary", use_container_width=True)
with col2:
    stop_btn = st.button("⏹️ Stop", use_container_width=True)

# Session State
if "monitoring" not in st.session_state:
    st.session_state.monitoring = False

if start_btn:
    st.session_state.monitoring = True
if stop_btn:
    st.session_state.monitoring = False

# Monitoring Loop
status_container = st.empty()
log_container = st.empty()

if st.session_state.monitoring:
    if not USING_CURL_CFFI:
        st.warning("⚠️ 'curl_cffi' not installed. Running in compatibility mode (higher risk of 403 blocks).")

    st.toast("Monitoring started...")
    
    while st.session_state.monitoring:
        is_live, msg = check_status(target_url)
        
        # UI Updates
        if is_live:
            status_container.success(msg)
            st.balloons()
            
            alert_msg = f"🚨 TICKETS LIVE! 🚨\n\nGo Book Now: {target_url}"
            
            if notify_method == "Telegram" and tg_token and tg_chat_id:
                send_telegram_alert(tg_token, tg_chat_id, alert_msg)
                st.write("✅ Telegram Alert Sent!")
                
            elif notify_method == "WhatsApp (CallMeBot)" and wa_phone and wa_key:
                send_whatsapp_alert(wa_phone, wa_key, alert_msg)
                st.write("✅ WhatsApp Alert Sent!")
            
            # Stop after success to avoid spamming
            st.session_state.monitoring = False
            break
        
        elif "Blocked" in msg:
            status_container.error(msg)
        else:
            status_container.info(msg)
        
        # Wait
        time.sleep(check_interval)
        # Rerun loop logic handled by Streamlit's reactive nature/while loop

    if not st.session_state.monitoring:
        st.write("Monitoring stopped.")
