import os
import time
import json
from pathlib import Path
from flask import Flask, jsonify
from instagrapi import Client
from dotenv import load_dotenv
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env file (अगर है तो)
load_dotenv()

# Environment variables
USERNAME = os.getenv('magmaxrich', 'magmaxrich')
PASSWORD = os.getenv('9113380244', '9113380244')
REPLY_MSG = os.getenv('REPLY_MESSAGE', 'धन्यवाद! 💖 आपके प्यार के लिए शुक्रिया!')
PORT = int(os.getenv('PORT', 3000))

# Flask app
app = Flask(__name__)

# Session file
SESSION_FILE = Path(f"session_{USERNAME}.json")

class InstagramBot:
    def __init__(self):
        self.cl = Client()
        self.cl.delay_range = [1, 3]
        self.running = True
        
    def login(self):
        """Login with session"""
        if SESSION_FILE.exists():
            logger.info("📂 Loading session...")
            self.cl.load_settings(SESSION_FILE)
            self.cl.login(USERNAME, PASSWORD)
        else:
            logger.info("🔑 First time login...")
            self.cl.login(USERNAME, PASSWORD)
            self.cl.dump_settings(SESSION_FILE)
        logger.info("✅ Login successful!")
        return True
    
    def check_messages(self):
        """Check for .love messages"""
        try:
            threads = self.cl.direct_threads(amount=5)
            for thread in threads:
                messages = self.cl.direct_messages(thread.id, amount=1)
                if messages:
                    msg = messages[0]
                    # अगर .love है और खुद ने नहीं भेजा
                    if (msg.text and msg.text.strip().lower() == '.love' 
                        and msg.user_id != self.cl.user_id):
                        
                        logger.info(f"💝 .love from {msg.user_id}")
                        # Reply भेजो
                        self.cl.direct_send(REPLY_MSG, [msg.user_id])
                        # Seen करो
                        self.cl.direct_thread_seen(thread.id, msg.id)
                        logger.info("✅ Reply sent!")
                        
        except Exception as e:
            logger.error(f"Error: {e}")
    
    def run(self):
        """Main loop"""
        self.login()
        logger.info("👂 Listening for .love messages...")
        
        while self.running:
            self.check_messages()
            time.sleep(5)  # हर 5 सेकंड में check करो

# Flask route for Render
@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'bot': 'Instagram 2-File Bot',
        'user': USERNAME
    })

# Start bot in background
import threading
bot = InstagramBot()
threading.Thread(target=bot.run, daemon=True).start()

# Run Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)