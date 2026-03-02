import os
import time
import threading
from flask import Flask
from instagrapi import Client
import logging

# --- Logging Setup (Taaki pata chale bot kya kar raha hai) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Active!"

def run_bot():
    cl = Client()
    # ⚠️ APNI DETAILS DAALEIN
    USERNAME = "magmaxrich"
    PASSWORD = "9113380244"
    
    try:
        logger.info("Login process start ho raha hai...")
        cl.login(USERNAME, PASSWORD)
        logger.info(f"✅ LOGIN SUCCESSFUL: {USERNAME}")
    except Exception as e:
        logger.error(f"❌ LOGIN FAILED: {e}")
        return

    TRIGGER = ".love"
    REPLY_TEXT = "❤️ Ye mera automated message hai! ❤️"
    
    processed_msg_ids = set()

    logger.info("🤖 Monitoring DMs for '.love' trigger...")

    while True:
        try:
            # Apne inbox ke top 10 messages uthao
            # 'amount=10' taaki koi message miss na ho
            messages = cl.direct_messages(amount=10)
            
            for msg in messages:
                # Agar ye naya message hai
                if msg.id not in processed_msg_ids:
                    
                    # Log har message ka text (Sirf check karne ke liye)
                    logger.info(f"Checking Message: '{msg.text}' from User ID: {msg.user_id}")
                    
                    # CONDITION: Agar message AAPNE bheja hai aur TRIGGER hai
                    if msg.user_id == cl.user_id and TRIGGER in msg.text.lower():
                        logger.info(f"🎯 TRIGGER DETECTED! Thread ID: {msg.thread_id}")
                        
                        # Reply bhej rahe hain
                        cl.direct_answer(msg.thread_id, REPLY_TEXT)
                        logger.info("✅ REPLY SENT SUCCESSFULLY!")
                        
                        # ID save karlo
                        processed_msg_ids.add(msg.id)
                    
                    # Purani IDs ko filter karte raho (Memory ke liye)
                    if len(processed_msg_ids) > 100:
                        processed_msg_ids.pop()

            time.sleep(12) # 12 seconds ka delay
            
        except Exception as e:
            logger.error(f"⚠️ Error in Loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    t = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port))
    t.start()
    run_bot()
