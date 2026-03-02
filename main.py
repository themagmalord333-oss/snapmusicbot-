import os
import json
import base64
import time
import threading
import logging
import requests
from flask import Flask, jsonify
from instagrapi import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USERNAME = os.environ.get('IG_USERNAME', 'magmaxrich')
PASSWORD = os.environ.get('9113380244')
SESSION_ID = os.environ.get('IG_SESSION_ID', '52659413459%3A8GvKhj070iUqIQ%3A21%3AAYjEhhY2ZCJyKlZA-s937zNTRHtbNHqstCGhDG9dNQ')
PORT = int(os.environ.get('PORT', 10000))

app = Flask(__name__)

class InstagramBot:
    def __init__(self):
        self.cl = Client()
        self.logged_in = False
        self.user_id = None
        
    def login_with_session_id(self):
        """Login using raw session ID"""
        try:
            logger.info("🔑 Trying login with session ID...")
            
            # Create session with cookie
            session = requests.Session()
            session.cookies.set("sessionid", SESSION_ID, domain=".instagram.com")
            
            # Get cookies dict
            cookies = session.cookies.get_dict()
            
            # Create settings for instagrapi
            settings = {
                "cookies": cookies,
                "user_agent": "Instagram 269.0.0.18.121 Android (28/9; 420dpi; 1080x1920; samsung; SM-G965F; star2qlte; qcom; en_US; 269.0.0.18.121)",
                "device_settings": {
                    "app_version": "269.0.0.18.121",
                    "android_version": 28,
                    "android_release": "9.0",
                    "manufacturer": "samsung",
                    "device": "star2qlte",
                    "model": "SM-G965F",
                    "dpi": "420dpi",
                    "resolution": "1080x1920",
                    "chipset": "qcom"
                }
            }
            
            # Load settings
            self.cl.set_settings(settings)
            
            # Verify by getting user_id
            self.user_id = self.cl.user_id_from_username(USERNAME)
            self.logged_in = True
            logger.info(f"✅ Login successful! User ID: {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Session ID login failed: {e}")
            return False
    
    def login_normal(self):
        """Normal login fallback"""
        try:
            logger.info("🔑 Trying normal login...")
            self.cl.login(USERNAME, PASSWORD)
            self.logged_in = True
            self.user_id = self.cl.user_id
            logger.info(f"✅ Normal login successful! User ID: {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Normal login failed: {e}")
            return False
    
    def login(self):
        """Try session ID first, then normal login"""
        if SESSION_ID and self.login_with_session_id():
            return True
        return self.login_normal()
    
    def check_messages(self):
        if not self.logged_in:
            return
        try:
            threads = self.cl.direct_threads(amount=5)
            for thread in threads:
                msgs = self.cl.direct_messages(thread.id, amount=1)
                if msgs:
                    msg = msgs[0]
                    if msg.text and msg.text.strip().lower() == '.love' and msg.user_id != self.user_id:
                        logger.info(f"💝 .love from {msg.user_id}")
                        self.cl.direct_send("धन्यवाद! 💖", [msg.user_id])
        except Exception as e:
            logger.error(f"Error: {e}")
    
    def run(self):
        if not self.login():
            logger.error("Login failed")
            return
        while True:
            self.check_messages()
            time.sleep(5)

bot = InstagramBot()
threading.Thread(target=bot.run, daemon=True).start()

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'user': USERNAME,
        'logged_in': bot.logged_in,
        'user_id': bot.user_id
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)