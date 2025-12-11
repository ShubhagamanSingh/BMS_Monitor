import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import smtplib
from email.message import EmailMessage
from datetime import datetime
import os

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="T20 Ticket Monitor",
    page_icon="🏏",
    layout="centered"
)

# --- DEFAULT CONFIGURATION ---
DEFAULT_URL = "https://in.bookmyshow.com/sports/delhi-icc-men-s-t20-wc-2026/ET00473562"
SUCCESS_KEYWORDS = ["Book Now", "Select Seats", "Buy Tickets"]
WAIT_KEYWORDS = ["Coming Soon", "Notify Me", "Interested", "Not Available"]

# --- FUNCTIONS ---

def send_email(sender_email, sender_password, receiver_email, event_url):
    """Sends an email notification using SMTP."""
    msg = EmailMessage()
    msg.set_content(f"""
    URGENT: CRICKET TICKETS MIGHT BE LIVE!
    
    The monitor detected a change in status for the T20 World Cup Match.
    
    Link: {event_url}
    
    Go book now!
    """)

    msg['Subject'] = '🏏 ALERT: Tickets Available (BMS Monitor)'
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        # Connect to Gmail SMTP (Standard port 587)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, f"Email failed: {e}"

def check_status(url):
    """Checks the BMS page for booking keywords."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()

            # Logic: Check if success keywords exist OR wait keywords disappeared
            found_success = any(keyword in text for keyword in SUCCESS_KEYWORDS)
            
            # Note: We are less aggressive with "wait keywords" disappearing to avoid false positives on simple page load errors
            # found_wait = any(keyword in text for keyword in WAIT_KEYWORDS) 

            if found_success:
                return True, "Booking keywords found!"
            
            return False, "Still waiting..."
        else:
            return False, f"Error: HTTP {response.status_code}"
    except Exception as e:
        return False, f"Error: {e}"

# --- UI LAYOUT ---

st.title("🏏 T20 World Cup Ticket Monitor")
st.markdown("Monitor **India vs Namibia (Feb 12, 2026)** and get an email when tickets open.")

# Sidebar for Credentials (safer UI)
with st.sidebar:
    st.header("📧 Email Settings")
    st.info("Use a Gmail App Password, not your login password.")
    sender_email = st.text_input("Sender Gmail", placeholder="you@gmail.com")
    sender_pass = st.text_input("Sender App Password", type="password", help="Go to Google Account > Security > 2-Step Verification > App Passwords")
    receiver_email = st.text_input("Receiver Email", value=sender_email)
    
    check_interval = st.slider("Check Interval (Seconds)", min_value=60, max_value=600, value=300)

# Main Area
target_url = st.text_input("Event URL", value=DEFAULT_URL)

col1, col2 = st.columns(2)
with col1:
    start_btn = st.button("Start Monitoring", type="primary")
with col2:
    stop_btn = st.button("Stop")

# Session state to handle loop
if "monitoring" not in st.session_state:
    st.session_state.monitoring = False

if start_btn:
    st.session_state.monitoring = True
if stop_btn:
    st.session_state.monitoring = False

# --- MAIN LOOP ---
status_placeholder = st.empty()
log_placeholder = st.empty()

if st.session_state.monitoring:
    if not (sender_email and sender_pass and receiver_email):
        st.error("Please fill in email credentials in the sidebar first!")
        st.session_state.monitoring = False
    else:
        st.success("Monitoring started... You can switch tabs, but keep this app active.")
        
        while st.session_state.monitoring:
            timestamp = datetime.now().strftime("%H:%M:%S")
            is_live, message = check_status(target_url)
            
            # Update UI
            status_placeholder.metric(label="Last Check", value=timestamp, delta=message if is_live else "Waiting")
            
            if is_live:
                st.balloons()
                st.warning("TICKETS DETECTED! Sending email...")
                
                success, email_msg = send_email(sender_email, sender_pass, receiver_email, target_url)
                
                if success:
                    st.success(f"Notification sent to {receiver_email}!")
                    st.session_state.monitoring = False # Stop after success
                    break
                else:
                    st.error(email_msg)
                    time.sleep(5) # Retry logic could go here
            
            # Wait
            time.sleep(check_interval)
            
            # Needed to keep the script running in some Streamlit environments
            # but in standard Streamlit, the loop blocks interactions. 
            # This is fine for a personal monitor.
