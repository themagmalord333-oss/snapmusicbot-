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
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import aiohttp
from aiohttp import web
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Application configuration"""
    BOT_TOKEN = os.getenv('8461918613:AAG0vYdmFl-Sag31h8NV0prt95rO0dXDMNw', '8461918613:AAG0vYdmFl-Sag31h8NV0prt95rO0dXDMNw') 
    OWNER_ID = int(os.getenv('7958364334', '0'))
    ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
    if OWNER_ID and OWNER_ID not in ADMIN_IDS:
        ADMIN_IDS.append(OWNER_ID)

    DATA_FILE = 'data.json'
    CHECK_INTERVAL = 300  # 5 minutes
    CONFIRMATION_THRESHOLD = 3
    MAX_USERNAMES_PER_USER = 20

    INSTA_HEADERS = {
        'User-Agent': 'Instagram 219.0.0.12.117 Android',
        'Accept': '*/*',
        'Accept-Language': 'en-US',
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

@dataclass
class InstagramProfile:
    username: str
    full_name: str = "N/A"
    followers: int = 0
    status: AccountStatus = AccountStatus.UNKNOWN

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
                pass
        return self._get_default_structure()

    def _get_default_structure(self) -> Dict:
        return {
            'users': {}, 'watch_list': {}, 'ban_list': {},
            'confirmation_counters': {}, 
            'stats': {'total_checks': 0, 'alerts_sent': 0}
        }

    def save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get_user(self, user_id: int) -> Optional[Dict]:
        return self.data['users'].get(str(user_id))

    def create_user(self, user_id: int, username: str = "") -> Dict:
        user = {
            'user_id': user_id, 'username': username, 'role': 'user',
            'subscription_expiry': None, 'watch_list': [], 'ban_list': []
        }
        self.data['users'][str(user_id)] = user
        self.save()
        return user

    def update_user(self, user_id: int, **kwargs):
        user = self.get_user(user_id)
        if user:
            user.update(kwargs)
            self.data['users'][str(user_id)] = user
            self.save()

    def add_to_watch(self, user_id: int, username: str) -> bool:
        user = self.get_user(user_id)
        if not user: return False
        username = username.lower().strip('@')
        if username not in user['watch_list']:
            user['watch_list'].append(username)
            self.update_user(user_id, **user)
            if username not in self.data['confirmation_counters']:
                self.data['confirmation_counters'][username] = {'status': 'unknown', 'count': 0}
            self.save()
            return True
        return False

    def remove_from_watch(self, user_id: int, username: str):
        user = self.get_user(user_id)
        if user and username in user['watch_list']:
            user['watch_list'].remove(username)
            self.update_user(user_id, **user)

    def add_to_ban(self, user_id: int, username: str):
        user = self.get_user(user_id)
        if user and username not in user['ban_list']:
            user['ban_list'].append(username)
            self.update_user(user_id, **user)

    def get_confirmation(self, username: str) -> Dict:
        return self.data['confirmation_counters'].get(username, {'status': 'unknown', 'count': 0})

    def update_confirmation(self, username: str, status: str, count: int):
        self.data['confirmation_counters'][username] = {'status': status, 'count': count}
        self.save()

    def reset_confirmation(self, username: str):
        self.update_confirmation(username, 'unknown', 0)

    def get_all_users(self) -> List[Dict]:
        return list(self.data['users'].values())

# ============================================================================
# INSTAGRAM MONITORING ENGINE
# ============================================================================

class InstagramMonitor:
    def __init__(self, db: DatabaseManager, bot):
        self.db = db
        self.bot = bot
        self.session = None

    async def get_profile(self, username: str) -> InstagramProfile:
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(headers=Config.INSTA_HEADERS)
            await asyncio.sleep(1) # Simulated API Delay
            username_lower = username.lower()
            if 'banned' in username_lower or 'suspended' in username_lower:
                return InstagramProfile(username=username, status=AccountStatus.BANNED)
            return InstagramProfile(username=username, status=AccountStatus.ACTIVE)
        except Exception as e:
            logging.error(f"Error fetching {username}: {e}")
            return InstagramProfile(username=username, status=AccountStatus.UNKNOWN)

    async def check_usernames(self):
        logging.info("Monitor loop started.")
        while True:
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
        conf = self.db.get_confirmation(username)
        current_status = profile.status.value
        
        new_count = conf['count'] + 1 if (current_status == conf['status'] and current_status != 'unknown') else 1
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
                # Remove from ban, but don't auto-watch again unless they want to.
                user['ban_list'].remove(username)
                self.db.update_user(user_id, **user)
                await self.send_alert(user_id, profile, "✅ **ACCOUNT UNBANNED**")

    async def send_alert(self, user_id: int, profile: InstagramProfile, header: str):
        text = f"{header}\n\n📧 **Username:** @{profile.username}\n🕐 Last Checked: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        try:
            await self.bot.send_message(chat_id=user_id, text=text, parse_mode='Markdown')
        except Exception as e:
            logging.error(f"Alert failed: {e}")

# ============================================================================
# BOT HANDLERS
# ============================================================================

class BotHandlers:
    def __init__(self, db: DatabaseManager):
        self.db = db

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not self.db.get_user(user.id):
            self.db.create_user(user.id, user.username)
        if user.id == Config.OWNER_ID:
            self.db.update_user(user.id, role='owner')
            
        await update.message.reply_text(f"👋 Welcome {user.first_name}!\nUse /watch <username> to track an account.")

    async def watch(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not context.args:
            await update.message.reply_text("⚠️ Usage: `/watch <username>`", parse_mode="Markdown")
            return
            
        username = context.args[0].replace('@', '')
        if self.db.add_to_watch(user_id, username):
            await update.message.reply_text(f"✅ Now watching: **@{username}**", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ Already watching **@{username}**", parse_mode="Markdown")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = self.db.get_user(update.effective_user.id)
        watch_list = user_data.get('watch_list', []) if user_data else []
        
        if not watch_list:
            await update.message.reply_text("📭 Your watchlist is empty.")
            return
            
        msg = "📊 **Your Watchlist:**\n\n" + "\n".join([f"• @{u}" for u in watch_list])
        await update.message.reply_text(msg, parse_mode="Markdown")

# ============================================================================
# MAIN ASYNC EXECUTION (RENDER COMPATIBLE)
# ============================================================================

async def start_dummy_server():
    """Starts a minimal aiohttp server to satisfy Render's Port Binding"""
    app = web.Application()
    app.add_routes([web.get('/', lambda r: web.json_response({"status": "running"}))])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Dummy Web Server started on port {port}")

async def main_loop():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    
    # 1. Start Dummy Server for Render
    await start_dummy_server()

    # 2. Init Core Systems
    db = DatabaseManager()
    application = Application.builder().token(Config.BOT_TOKEN).build()
    monitor = InstagramMonitor(db, application.bot)
    handlers = BotHandlers(db)

    # 3. Add Commands
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("watch", handlers.watch))
    application.add_handler(CommandHandler("status", handlers.status))

    # 4. Start Bot Manually (Bypassing .run_polling bug)
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    logging.info("Bot is polling...")

    # 5. Start Instagram Monitor Loop in Background
    asyncio.create_task(monitor.check_usernames())

    # 6. Keep the script alive forever
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Standard boilerplate for running an asyncio program
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        pass