import os
import json
import base64
import time
import threading
import logging
from flask import Flask, jsonify
from instagrapi import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USERNAME = os.environ.get('magmaxrich')
PASSWORD = os.environ.get('9113380244')
SESSION_BASE64 = os.environ.get('52659413459%3Ah6jvs5WzdCkNgM%3A17%3AAYirQNsCH8kMuZxBK_xM_HZywn25OW3HZRy_vmnjPA')
PORT = int(os.environ.get('PORT', 10000))

app = Flask(__name__)

class InstagramBot:
    def __init__(self):
        self.cl = Client()
        self.cl.delay_range = [1, 3]
        self.logged_in = False
        self.user_id = None

    def login_with_base64_session(self):
        """Login using base64 session from env"""
        if not SESSION_BASE64:
            return False
        
        try:
            logger.info("🔑 Trying base64 session login...")
            session_json = base64.b64decode(SESSION_BASE64).decode()
            session_data = json.loads(session_json)
            
            self.cl.set_settings(session_data)
            self.cl.get_timeline_feed()  # Just to verify session works
            
            # Get user info
            self.user_id = self.cl.user_id
            self.logged_in = True
            logger.info(f"✅ Base64 session login successful! User ID: {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Base64 session failed: {e}")
            return False

    def login_fresh(self):
        """Fresh login as fallback"""
        try:
            logger.info("🔑 Trying fresh login...")
            self.cl.login(USERNAME, PASSWORD)
            self.logged_in = True
            self.user_id = self.cl.user_id
            logger.info(f"✅ Fresh login successful! User ID: {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Fresh login failed: {e}")
            return False

    def login(self):
        """Try base64 session first, then fresh login"""
        if self.login_with_base64_session():
            return True
        return self.login_fresh()

    def run(self):
        if not self.login():
            logger.error("❌ All login methods failed. Bot exiting.")
            return
        
        logger.info("👂 Bot listening for .love messages...")
        while True:
            try:
                # Just keep-alive and message checking
                threads = self.cl.direct_threads(amount=3)
                logger.debug(f"Found {len(threads)} threads")
                
                for thread in threads:
                    msgs = self.cl.direct_messages(thread.id, amount=1)
                    if msgs:
                        msg = msgs[0]
                        if msg.text and msg.text.strip().lower() == '.love' and msg.user_id != self.user_id:
                            logger.info(f"💝 .love from {msg.user_id}")
                            self.cl.direct_send("धन्यवाद! 💖", [msg.user_id])
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(30)

# Create bot
bot = InstagramBot()

# Start bot thread
def run_bot():
    bot.run()

thread = threading.Thread(target=run_bot, daemon=True)
thread.start()

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'user': USERNAME,
        'logged_in': bot.logged_in,
        'user_id': bot.user_id,
        'thread_alive': thread.is_alive()
    })

@app.route('/debug')
def debug():
    return jsonify({
        'env': {
            'username': bool(USERNAME),
            'password': bool(PASSWORD),
            'session_base64': bool(SESSION_BASE64),
            'session_base64_length': len(SESSION_BASE64) if SESSION_BASE64 else 0
        },
        'bot': {
            'logged_in': bot.logged_in,
            'user_id': bot.user_id
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)