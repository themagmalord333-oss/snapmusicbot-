import os
import sys
import time
import threading
import logging
from flask import Flask, jsonify
from instagrapi import Client

# Force logs to show immediately
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

# Print startup banner
print("\n" + "="*50)
print("🤖 BOT STARTING - DEBUG MODE")
print("="*50 + "\n")

# Get env vars
USERNAME = os.environ.get('frexxy_07')
PASSWORD = os.environ.get('NAEEM ANSARI 922932')
PORT = int(os.environ.get('PORT', 10000))

print(f"📱 Username from env: {USERNAME}")
print(f"🔑 Password set: {'Yes' if PASSWORD else 'No'}")
print(f"🌍 Port: {PORT}")

if not USERNAME or not PASSWORD:
    print("❌ CRITICAL: Username or password missing!")
    sys.exit(1)

app = Flask(__name__)

class DebugBot:
    def __init__(self):
        print("🔧 Initializing bot...")
        self.cl = Client()
        self.logged_in = False
        self.user_id = None
        self.error = None
        
    def login(self):
        print("🔑 Attempting login...")
        try:
            # Try login
            self.cl.login(USERNAME, PASSWORD)
            self.logged_in = True
            self.user_id = self.cl.user_id
            print(f"✅ LOGIN SUCCESSFUL! User ID: {self.user_id}")
            return True
        except Exception as e:
            self.error = str(e)
            print(f"❌ LOGIN FAILED: {e}")
            
            # Specific error handling
            if "challenge" in str(e).lower():
                print("⚠️ Instagram wants verification! Check your phone.")
            elif "bad password" in str(e).lower():
                print("⚠️ Wrong password!")
            elif "rate limit" in str(e).lower():
                print("⚠️ Rate limited! Wait 10-15 minutes.")
            return False
    
    def run(self):
        print("🏃‍♂️ Bot thread started!")
        if self.login():
            print("👂 Listening for messages...")
            while True:
                try:
                    # Keep alive
                    time.sleep(10)
                except Exception as e:
                    print(f"Error in loop: {e}")
        else:
            print("💀 Login failed, thread exiting...")

# Create bot
print("🚀 Creating bot instance...")
bot = DebugBot()

# Start thread with error catching
def thread_target():
    try:
        bot.run()
    except Exception as e:
        print(f"🔥 THREAD CRASHED: {e}")
        import traceback
        traceback.print_exc()

print("🧵 Starting thread...")
thread = threading.Thread(target=thread_target, daemon=True)
thread.start()
print(f"✅ Thread started, alive: {thread.is_alive()}")

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'user': USERNAME,
        'logged_in': bot.logged_in,
        'user_id': bot.user_id,
        'thread_alive': thread.is_alive(),
        'error': bot.error
    })

@app.route('/debug')
def debug():
    return jsonify({
        'env': {
            'username': USERNAME,
            'password_exists': bool(PASSWORD)
        },
        'bot': {
            'logged_in': bot.logged_in,
            'user_id': bot.user_id,
            'error': bot.error
        },
        'thread': {
            'alive': thread.is_alive(),
            'ident': thread.ident
        }
    })

print(f"🌍 Flask server starting on port {PORT}...")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)