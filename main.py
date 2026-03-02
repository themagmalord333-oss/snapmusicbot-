import os
import time
import threading
import logging
from pathlib import Path
from flask import Flask, jsonify
from instagrapi import Client

# 🔥 Detailed logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
USERNAME = os.environ.get('magmaxrich')
PASSWORD = os.environ.get('9113380244')
REPLY_MSG = os.environ.get('REPLY_MESSAGE', 'धन्यवाद! 💖')
PORT = int(os.environ.get('PORT', 10000))

# Session file path
SESSION_FILE = Path(f"session_{USERNAME}.json")

# Flask app
app = Flask(__name__)

class InstagramBot:
    def __init__(self):
        self.cl = Client()
        self.cl.delay_range = [1, 3]
        self.logged_in = False
        self.user_id = None
        
    def login(self):
        """Login with session"""
        try:
            # Try to load existing session
            if SESSION_FILE.exists():
                logger.info(f"📂 Loading session from {SESSION_FILE}")
                self.cl.load_settings(SESSION_FILE)
                self.cl.login(USERNAME, PASSWORD)
                logger.info("✅ Session loaded successfully!")
            else:
                logger.info("🔑 No session found. First time login...")
                self.cl.login(USERNAME, PASSWORD)
                # Save session
                self.cl.dump_settings(SESSION_FILE)
                logger.info(f"✅ Login successful! Session saved to {SESSION_FILE}")
            
            self.logged_in = True
            self.user_id = self.cl.user_id
            logger.info(f"👤 Logged in as: {USERNAME} (ID: {self.user_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            return False
    
    def check_messages(self):
        """Check for .love messages"""
        if not self.logged_in:
            logger.warning("⚠️ Not logged in, skipping message check")
            return
        
        try:
            logger.debug("Checking for new messages...")
            threads = self.cl.direct_threads(amount=5)
            
            for thread in threads:
                messages = self.cl.direct_messages(thread.id, amount=1)
                
                if messages:
                    msg = messages[0]
                    logger.debug(f"Message from {msg.user_id}: {msg.text}")
                    
                    # Check if it's .love and not from self
                    if (msg.text and 
                        msg.text.strip().lower() == '.love' and 
                        msg.user_id != self.user_id):
                        
                        logger.info(f"💝 .love received from user {msg.user_id}!")
                        
                        # Send reply
                        self.cl.direct_send(REPLY_MSG, [msg.user_id])
                        logger.info(f"✅ Reply sent: {REPLY_MSG}")
                        
                        # Mark as seen
                        self.cl.direct_thread_seen(thread.id, msg.id)
                        
        except Exception as e:
            logger.error(f"Error checking messages: {e}")
    
    def run(self):
        """Main loop"""
        logger.info("🤖 Bot starting...")
        
        if not self.login():
            logger.error("❌ Could not login. Bot will retry in 60 seconds...")
            time.sleep(60)
            return
        
        logger.info("👂 Bot is now listening for .love messages...")
        logger.info(f"📝 Reply message: {REPLY_MSG}")
        
        while True:
            try:
                self.check_messages()
                time.sleep(5)  # Check every 5 seconds
            except KeyboardInterrupt:
                logger.info("👋 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(30)

# Create bot instance
bot = InstagramBot()

# Flask routes
@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'bot': 'Instagram Bot',
        'user': USERNAME,
        'logged_in': bot.logged_in,
        'user_id': bot.user_id,
        'session_file_exists': SESSION_FILE.exists()
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/debug')
def debug():
    """Debug endpoint to check bot status"""
    return jsonify({
        'username': USERNAME,
        'logged_in': bot.logged_in,
        'user_id': bot.user_id,
        'session_file': str(SESSION_FILE),
        'session_exists': SESSION_FILE.exists(),
        'session_size': SESSION_FILE.stat().st_size if SESSION_FILE.exists() else 0
    })

# Start bot in background thread
def start_bot():
    bot.run()

thread = threading.Thread(target=start_bot, daemon=True)
thread.start()
logger.info("🚀 Bot thread started")

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)