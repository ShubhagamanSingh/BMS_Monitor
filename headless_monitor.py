import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage
import os
import sys

# --- CONFIGURATION ---
# We get these from GitHub "Secrets" (Environment Variables)
TARGET_URL = "https://in.bookmyshow.com/sports/canada-vs-united-arab-emirates-icc-men-s-t20-wc-2026/ET00474012"
GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_PASS = os.environ.get('GMAIL_PASS')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL')

SUCCESS_KEYWORDS = ["Login to book", "Book Now", "Select Seats", "Buy Tickets"]

def send_alert():
    msg = EmailMessage()
    msg.set_content(f"""
    URGENT: CRICKET TICKETS DETECTED!
    
    The GitHub Action monitor found 'Book Now' keywords on the page.
    
    Link: {TARGET_URL}
    
    Go book now!
    """)

    msg['Subject'] = '🏏 URGENT: Tickets Available (GitHub Action)'
    msg['From'] = GMAIL_USER
    msg['To'] = RECEIVER_EMAIL

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_status():
    print(f"Checking URL: {TARGET_URL}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            
            # Check for success keywords
            if any(keyword in text for keyword in SUCCESS_KEYWORDS):
                print("SUCCESS: Booking keywords found!")
                send_alert()
                return True
            else:
                print("Status: Still waiting (Keywords not found).")
                return False
        else:
            print(f"Error: Status code {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if not GMAIL_USER or not GMAIL_PASS:
        print("Error: GMAIL_USER or GMAIL_PASS not found in environment variables.")
        sys.exit(1)
        
    check_status()
