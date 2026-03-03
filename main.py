import os
import sys
import time
import threading
import logging
from flask import Flask, jsonify
from instagrapi import Client  # 'instagramp' nahi, 'instagrapi' sahi spelling

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

print("\n" + "="*50)
print("🤖 BOT STARTING")
print("="*50 + "\n")

# ✅ SAHI TARIQA - Environment variable KEYS use karo
USERNAME = os.environ.get('IG_USERNAME')      # 'frexxy_07' nahi
PASSWORD = os.environ.get('IG_PASSWORD')      # 'NAEEM ANSARI 922932' nahi
PORT = int(os.environ.get('PORT', 10000))

print(f"📱 Username from env: {USERNAME}")
print(f"🔑 Password set: {'Yes' if PASSWORD else 'No'}")
print(f"🌍 Port: {PORT}")

if not USERNAME or not PASSWORD:
    print("❌ CRITICAL: Username or password missing!")
    print("👉 Render Dashboard mein Environment Variables set karo:")
    print("   IG_USERNAME = frexxy_07")
    print("   IG_PASSWORD = NAEEM ANSARI 922932")
    sys.exit(1)

app = Flask(__name__)

class InstagramBot:
    def __init__(self):
        self.cl = Client()
        self.logged_in = False
        self.user_id = None
        
    def login(self):
        try:
            print(f"🔑 Logging in as {USERNAME}...")
            self.cl.login(USERNAME, PASSWORD)
            self.logged_in = True
            self.user_id = self.cl.user_id
            print(f"✅ Login successful! User ID: {self.user_id}")
            return True
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    def run(self):
        if self.login():
            print("👂 Bot is running...")
            while True:
                time.sleep(10)

bot = InstagramBot()

def start_bot():
    bot.run()

thread = threading.Thread(target=start_bot, daemon=True)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)