"""
Professional Instagram Username Monitor Bot
Enterprise Grade - SaaS Style
Author: @proxyfxc
Channel: @proxydominates
"""

import os
import json
import asyncio
import logging
import datetime
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from flask import Flask, jsonify
import aiohttp
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Application configuration"""
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE') 
    OWNER_ID = int(os.getenv('OWNER_ID', '0'))
    ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
    if OWNER_ID and OWNER_ID not in ADMIN_IDS:
        ADMIN_IDS.append(OWNER_ID)

    DATA_FILE = 'data.json'
    CHECK_INTERVAL = 300  # 5 minutes in seconds
    CONFIRMATION_THRESHOLD = 3
    MAX_USERNAMES_PER_USER = 20

    # Instagram API simulation (replace with actual API)
    INSTA_API_URL = "https://i.instagram.com/api/v1/users/web_profile_info/?username={}"
    INSTA_HEADERS = {
        'User-Agent': 'Instagram 219.0.0.12.117 Android',
        'Accept': '*/*',
        'Accept-Language': 'en-US',
        'Accept-Encoding': 'gzip, deflate',
    }

# ============================================================================
# DATA MODELS
# ============================================================================

class UserRole(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    USER = "user"

class AccountStatus(Enum):
    ACTIVE = "active"
    BANNED = "banned"
    UNKNOWN = "unknown"
    CHECKING = "checking"

@dataclass
class InstagramProfile:
    """Instagram profile data"""
    username: str
    full_name: str = "N/A"
    followers: int = 0
    following: int = 0
    posts: int = 0
    is_private: bool = False
    is_verified: bool = False
    biography: str = ""
    profile_pic_url: str = ""
    status: AccountStatus = AccountStatus.UNKNOWN
    last_checked: Optional[str] = None

@dataclass
class MonitoredUser:
    """User data structure"""
    user_id: int
    username: str = ""
    role: UserRole = UserRole.USER
    subscription_expiry: Optional[str] = None
    watch_list: List[str] = None
    ban_list: List[str] = None
    created_at: str = ""

    def __post_init__(self):
        if self.watch_list is None:
            self.watch_list = []
        if self.ban_list is None:
            self.ban_list = []

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """Persistent JSON database manager"""

    def __init__(self, file_path: str = Config.DATA_FILE):
        self.file_path = file_path
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        if Path(self.file_path).exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._get_default_structure()
        return self._get_default_structure()

    def _get_default_structure(self) -> Dict:
        return {
            'users': {}, 'watch_list': {}, 'ban_list': {},
            'confirmation_counters': {}, 'username_cache': {},
            'stats': {'total_checks': 0, 'alerts_sent': 0, 'created_at': datetime.datetime.now().isoformat()}
        }

    def save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get_user(self, user_id: int) -> Optional[Dict]:
        return self.data['users'].get(str(user_id))

    def create_user(self, user_id: int, username: str = "") -> Dict:
        user = {
            'user_id': user_id, 'username': username, 'role': 'user',
            'subscription_expiry': None, 'watch_list': [], 'ban_list': [],
            'created_at': datetime.datetime.now().isoformat()
        }
        self.data['users'][str(user_id)] = user
        self.save()
        return user

    def update_user(self, user_id: int, **kwargs) -> Optional[Dict]:
        user = self.get_user(user_id)
        if user:
            user.update(kwargs)
            self.data['users'][str(user_id)] = user
            self.save()
            return user
        return None

    def add_to_watch(self, user_id: int, username: str) -> bool:
        user = self.get_user(user_id)
        if not user: return False
        username = username.lower().strip('@')
        if username not in user['watch_list']:
            user['watch_list'].append(username)
            self.update_user(user_id, **user)
            if username not in self.data['confirmation_counters']:
                self.data['confirmation_counters'][username] = {'status': 'unknown', 'count': 0, 'last_check': None}
            self.save()
            return True
        return False

    def remove_from_watch(self, user_id: int, username: str) -> bool:
        user = self.get_user(user_id)
        if user and username in user['watch_list']:
            user['watch_list'].remove(username)
            self.update_user(user_id, **user)
            return True
        return False

    def add_to_ban(self, user_id: int, username: str) -> bool:
        user = self.get_user(user_id)
        if not user: return False
        username = username.lower().strip('@')
        if username not in user['ban_list']:
            user['ban_list'].append(username)
            self.update_user(user_id, **user)
            self.save()
        return True

    def remove_from_ban(self, user_id: int, username: str) -> bool:
        user = self.get_user(user_id)
        if user and username in user['ban_list']:
            user['ban_list'].remove(username)
            self.update_user(user_id, **user)
            return True
        return False

    def update_confirmation(self, username: str, status: str, count: int) -> Dict:
        self.data['confirmation_counters'][username] = {
            'status': status, 'count': count, 'last_check': datetime.datetime.now().isoformat()
        }
        self.save()
        return self.data['confirmation_counters'][username]

    def get_confirmation(self, username: str) -> Dict:
        return self.data['confirmation_counters'].get(username, {'status': 'unknown', 'count': 0, 'last_check': None})

    def reset_confirmation(self, username: str):
        self.update_confirmation(username, 'unknown', 0)

    def is_subscription_active(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if not user: return False
        if user['role'] in ['owner', 'admin']: return True
        expiry = user.get('subscription_expiry')
        if not expiry: return False
        try:
            return datetime.datetime.fromisoformat(expiry) > datetime.datetime.now()
        except:
            return False

    def extend_subscription(self, user_id: int, days: int) -> bool:
        user = self.get_user(user_id)
        if not user: return False
        now = datetime.datetime.now()
        if user.get('subscription_expiry'):
            try:
                current = datetime.datetime.fromisoformat(user['subscription_expiry'])
                new_expiry = (current if current > now else now) + datetime.timedelta(days=days)
            except:
                new_expiry = now + datetime.timedelta(days=days)
        else:
            new_expiry = now + datetime.timedelta(days=days)
        user['subscription_expiry'] = new_expiry.isoformat()
        self.update_user(user_id, **user)
        return True

    def get_all_users(self) -> List[Dict]:
        return list(self.data['users'].values())


# ============================================================================
# INSTAGRAM MONITORING ENGINE
# ============================================================================

class InstagramMonitor:
    def __init__(self, db: DatabaseManager, bot_app: Application):
        self.db = db
        self.bot = bot_app.bot
        self.is_running = True
        self.session = None

    async def get_profile(self, username: str) -> InstagramProfile:
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(headers=Config.INSTA_HEADERS)
            await asyncio.sleep(1) # Simulating API
            username_lower = username.lower()
            if 'banned' in username_lower or 'suspended' in username_lower:
                return InstagramProfile(username=username, status=AccountStatus.BANNED)
            return InstagramProfile(
                username=username, full_name="John Doe", followers=1000,
                following=500, posts=50, is_private=False, is_verified=False,
                biography=f"User {username}", status=AccountStatus.ACTIVE
            )
        except Exception as e:
            logging.error(f"Error fetching profile {username}: {e}")
            return InstagramProfile(username=username, status=AccountStatus.UNKNOWN)

    async def check_usernames(self):
        while self.is_running:
            try:
                all_usernames = set()
                for user in self.db.get_all_users():
                    all_usernames.update(user.get('watch_list', []))
                for username in all_usernames:
                    await self.check_single_username(username)
                    await asyncio.sleep(2)
                self.db.data['stats']['total_checks'] += len(all_usernames)
                self.db.save()
            except Exception as e:
                logging.error(f"Loop error: {e}")
            await asyncio.sleep(Config.CHECK_INTERVAL)

    async def check_single_username(self, username: str):
        profile = await self.get_profile(username)
        confirmation = self.db.get_confirmation(username)
        current_status = profile.status.value
        previous_status = confirmation['status']
        current_count = confirmation['count']

        new_count = current_count + 1 if (current_status == previous_status and current_status != 'unknown') else (1 if current_status != 'unknown' else 0)
        self.db.update_confirmation(username, current_status, new_count)

        if new_count >= Config.CONFIRMATION_THRESHOLD:
            await self.handle_status_change(username, profile, current_status)
            self.db.reset_confirmation(username)

    async def handle_status_change(self, username: str, profile: InstagramProfile, new_status: str):
        for user in self.db.get_all_users():
            user_id = user['user_id']
            if new_status == 'banned' and username in user.get('watch_list', []):
                self.db.remove_from_watch(user_id, username)
                self.db.add_to_ban(user_id, username)
                await self.send_alert(user_id, profile, "🚫 **ACCOUNT BANNED**")
            elif new_status == 'active' and username in user.get('ban_list', []):
                self.db.remove_from_ban(user_id, username)
                self.db.add_to_watch(user_id, username)
                await self.send_alert(user_id, profile, "✅ **ACCOUNT UNBANNED**")

    async def send_alert(self, user_id: int, profile: InstagramProfile, header: str):
        text = f"{header}\n\n👤 **Name:** {profile.full_name}\n📧 **Username:** @{profile.username}\n👥 **Followers:** {profile.followers}\n🕐 Last Checked: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        try:
            await self.bot.send_message(chat_id=user_id, text=text, parse_mode='Markdown')
            self.db.data['stats']['alerts_sent'] += 1
        except Exception as e:
            logging.error(f"Alert failed to {user_id}: {e}")

# ============================================================================
# FLASK KEEP-ALIVE SERVER
# ============================================================================

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({'status': 'running', 'service': 'Instagram Monitor Bot'})

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))

# ============================================================================
# TELEGRAM BOT HANDLERS
# ============================================================================

class BotHandlers:
    def __init__(self, db: DatabaseManager, monitor: InstagramMonitor):
        self.db = db
        self.monitor = monitor

    def _check_access(self, user_id: int, required_role: str = 'user') -> Tuple[bool, str]:
        user = self.db.get_user(user_id)
        if not user:
            return False, "❌ You are not registered. Use /start to begin."
        if user['role'] == 'owner': return True, ""
        if user['role'] == 'admin' and required_role in ['user', 'admin']: return True, ""
        if required_role == 'admin': return False, "❌ Admin access required."
        if not self.db.is_subscription_active(user_id):
            return False, "❌ Your subscription has expired. Contact admin."
        return True, ""

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not self.db.get_user(user.id):
            self.db.create_user(user.id, user.username)
        
        # Auto-grant owner role based on config
        if user.id == Config.OWNER_ID:
            self.db.update_user(user.id, role='owner')
            
        await update.message.reply_text(
            f"👋 Welcome {user.first_name} to the Enterprise Instagram Monitor!\n\n"
            "Use /watch <username> to start tracking an account."
        )

    async def watch(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        has_access, msg = self.check_access(user_id)
        if not has_access:
            await update.message.reply_text(msg)
            return

        if not context.args:
            await update.message.reply_text("⚠️ Usage: `/watch <username>`", parse_mode="Markdown")
            return
            
        username = context.args[0].replace('@', '')
        user_data = self.db.get_user(user_id)
        
        if len(user_data.get('watch_list', [])) >= Config.MAX_USERNAMES_PER_USER and user_data['role'] not in ['admin', 'owner']:
            await update.message.reply_text("❌ You have reached your watch limit.")
            return

        if self.db.add_to_watch(user_id, username):
            await update.message.reply_text(f"✅ Now watching: **@{username}**", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ You are already watching **@{username}**", parse_mode="Markdown")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        if not user_data: return

        watch_list = user_data.get('watch_list', [])
        if not watch_list:
            await update.message.reply_text("📭 Your watchlist is empty.")
            return

        msg = "📊 **Your Watchlist Status:**\n\n"
        for user in watch_list:
            msg += f"• @{user}\n"
        await update.message.reply_text(msg, parse_mode="Markdown")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def post_init(application: Application):
    """Start background tasks when the bot starts"""
    # Create the monitor instance attached to the app context
    monitor = application.bot_data['monitor']
    asyncio.create_task(monitor.check_usernames())

def main():
    # 1. Initialize Logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # 2. Initialize Core Components
    db = DatabaseManager()
    
    # 3. Setup Bot Application
    bot_app = Application.builder().token(Config.BOT_TOKEN).post_init(post_init).build()
    monitor = InstagramMonitor(db, bot_app)
    
    # Store monitor in bot_data for access in post_init
    bot_app.bot_data['monitor'] = monitor 
    
    # 4. Setup Handlers
    handlers = BotHandlers(db, monitor)
    bot_app.add_handler(CommandHandler("start", handlers.start))
    bot_app.add_handler(CommandHandler("watch", handlers.watch))
    bot_app.add_handler(CommandHandler("status", handlers.status))
    
    # 5. Start Flask keep-alive server in background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logging.info("Flask keep-alive server started.")
    
    # 6. Run Telegram Bot (Blocking)
    logging.info("Starting Telegram bot polling...")
    bot_app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
