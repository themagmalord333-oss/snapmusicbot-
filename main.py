import os
import time
import threading
from flask import Flask
from instagrapi import Client
import logging

# Logging for Render Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Active!"

def run_bot():
    cl = Client()
    
    # 📱 Real Android Device jaisa dikhne ke liye User-Agent
    cl.set_user_agent("Instagram 219.0.0.12.117 Android (29/10; 480dpi; 1080x2202; Xiaomi; Redmi Note 9 Pro; joyeuse; qcom; en_US; 340011804)")

    USERNAME = "frexxy_07" # Aapki ID
    PASSWORD = "NAEEM ANSARI 922932" # Apna sahi password yahan dalein
    SESSION_FILE = "session_insta.json"

    # --- Login Logic ---
    try:
        if os.path.exists(SESSION_FILE):
            cl.load_settings(SESSION_FILE)
            logger.info("Session file mil gayi, login kar raha hoon...")
        
        cl.login(USERNAME, PASSWORD)
        cl.dump_settings(SESSION_FILE) # Naya session save karein
        logger.info(f"✅ LOGIN SUCCESS: {cl.user_id}")
    except Exception as e:
        logger.error(f"❌ LOGIN FAILED: {e}")
        return

    TRIGGER = ".love"
    REPLY_TEXT = "❤️ Ye mera automated message hai! Swagat hai. ❤️"
    processed_ids = set()

    logger.info("🤖 Bot monitoring started...")

    while True:
        try:
            # Apne inbox ke messages fetch karein
            messages = cl.direct_messages(amount=10)
            
            for msg in messages:
                if msg.id not in processed_ids:
                    # Logic: Agar message AAPNE bheja hai aur TRIGGER word hai
                    if msg.user_id == cl.user_id and TRIGGER in msg.text.lower():
                        logger.info(f"🎯 Trigger detected in Thread: {msg.thread_id}")
                        
                        # Automated Reply
                        cl.direct_answer(msg.thread_id, REPLY_TEXT)
                        logger.info("✅ Reply sent!")
                        
                        processed_ids.add(msg.id)
            
            # 15 seconds ka gap (Safety ke liye)
            time.sleep(15)
            
        except Exception as e:
            logger.error(f"⚠️ Loop Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    # Render ke liye Flask thread
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()
    
    # Bot start karein
    run_bot()
