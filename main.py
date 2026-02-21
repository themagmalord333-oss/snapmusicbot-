import instaloader
from instabot import Bot
import time
import os
import shutil
import sys
import logging
from datetime import datetime

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class InstagramBot:
    def __init__(self):
        self.bot = Bot()
        self.L = instaloader.Instaloader()
        self.username = os.environ.get('INSTAGRAM_USERNAME', '')
        self.password = os.environ.get('INSTAGRAM_PASSWORD', '')
        self.target = os.environ.get('TARGET_USERNAME', '')
        self.message = os.environ.get('MESSAGE', 'Hello!')
        self.count = int(os.environ.get('MESSAGE_COUNT', '5'))
        
    def setup_session(self):
        """Session setup using environment variables"""
        try:
            # Pehle session file check karo
            session_file = f"{self.username}.session"
            
            if os.path.exists(session_file):
                logging.info(f"✅ Session file found: {session_file}")
                self.L.load_session_from_file(self.username)
                self.bot.login(username=self.username, use_cookie=True)
                return True
            else:
                logging.info("📝 Creating new session...")
                return self.create_new_session()
                
        except Exception as e:
            logging.error(f"❌ Session error: {e}")
            return False
    
    def create_new_session(self):
        """Create new session using environment credentials"""
        try:
            if not self.password:
                logging.error("❌ Password not found in environment variables")
                return False
                
            # Instaloader login
            self.L.login(self.username, self.password)
            self.L.save_session_to_file()
            logging.info(f"✅ Session saved: {self.username}.session")
            
            # Instabot login
            self.bot.login(username=self.username, password=self.password)
            logging.info("✅ Instabot login successful")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Login failed: {e}")
            return False
    
    def send_bulk_messages(self):
        """Send messages with error handling"""
        try:
            # Target user ID find karo
            user_id = self.bot.get_user_id_from_username(self.target)
            logging.info(f"✅ Target found: {self.target} (ID: {user_id})")
            
            logging.info(f"📤 Sending {self.count} messages to {self.target}...")
            
            for i in range(self.count):
                try:
                    self.bot.send_message(self.message, [user_id])
                    logging.info(f"✓ Message {i+1}/{self.count} sent")
                    
                    # Smart delay
                    if (i + 1) % 10 == 0:
                        logging.info("⏸️ Taking 30 sec break...")
                        time.sleep(30)
                    else:
                        time.sleep(2)
                        
                except Exception as e:
                    logging.error(f"❌ Failed to send message {i+1}: {e}")
                    time.sleep(5)
                    continue
            
            logging.info(f"✅ All {self.count} messages sent successfully!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Fatal error: {e}")
            return False
    
    def run_once(self):
        """Run bot once and exit"""
        logging.info("="*50)
        logging.info("🔥 INSTAGRAM BOT STARTING 🔥")
        logging.info("="*50)
        
        if not self.username:
            logging.error("❌ INSTAGRAM_USERNAME not set in environment")
            return False
            
        logging.info(f"👤 Logging in as: {self.username}")
        
        if self.setup_session():
            if self.target and self.message:
                success = self.send_bulk_messages()
                logging.info(f"📊 Final status: {'✅ Success' if success else '❌ Failed'}")
                return success
            else:
                logging.warning("⚠️ TARGET_USERNAME or MESSAGE not set")
                return True  # Not a failure, just no messages
        else:
            logging.error("❌ Login failed")
            return False

def keep_alive():
    """Keep the bot running (for web service)"""
    from flask import Flask, jsonify
    import threading
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return jsonify({
            'status': 'alive',
            'bot': 'running',
            'time': datetime.now().isoformat()
        })
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})
    
    # Run Flask in a separate thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))).start()
    logging.info("🌐 Web server started for keep-alive")

def main():
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['once', 'web'], default='web')
    args = parser.parse_args()
    
    bot = InstagramBot()
    
    if args.mode == 'web':
        # Web mode - keep running
        keep_alive()
        
        # Run bot once immediately
        bot.run_once()
        
        # Schedule next run? (optional)
        # For now, just keep web server running
        while True:
            time.sleep(3600)  # Sleep for 1 hour
            # Run again? Uncomment below:
            # bot.run_once()
            
    else:
        # Once mode - run and exit
        success = bot.run_once()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()