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
import requests
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
import aiohttp

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Application configuration"""
    BOT_TOKEN = os.getenv('8461918613:AAG0vYdmFl-Sag31h8NV0prt95rO0dXDMNw')
    OWNER_ID = int(os.getenv('7727470646', '0'))
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

@dataclass
class ConfirmationCounter:
    """Confirmation counter for anti-false-alert system"""
    username: str
    status: AccountStatus
    count: int = 0
    last_check: str = ""

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """Persistent JSON database manager"""
    
    def __init__(self, file_path: str = Config.DATA_FILE):
        self.file_path = file_path
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load data from JSON file"""
        if Path(self.file_path).exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._get_default_structure()
        return self._get_default_structure()
    
    def _get_default_structure(self) -> Dict:
        """Get default data structure"""
        return {
            'users': {},
            'watch_list': {},
            'ban_list': {},
            'confirmation_counters': {},
            'username_cache': {},
            'stats': {
                'total_checks': 0,
                'alerts_sent': 0,
                'created_at': datetime.datetime.now().isoformat()
            }
        }
    
    def save(self):
        """Save data to JSON file"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    # User Management
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        return self.data['users'].get(str(user_id))
    
    def create_user(self, user_id: int, username: str = "") -> Dict:
        """Create new user"""
        user = {
            'user_id': user_id,
            'username': username,
            'role': 'user',
            'subscription_expiry': None,
            'watch_list': [],
            'ban_list': [],
            'created_at': datetime.datetime.now().isoformat()
        }
        self.data['users'][str(user_id)] = user
        self.save()
        return user
    
    def update_user(self, user_id: int, **kwargs) -> Optional[Dict]:
        """Update user data"""
        user = self.get_user(user_id)
        if user:
            user.update(kwargs)
            self.data['users'][str(user_id)] = user
            self.save()
            return user
        return None
    
    # Watch/Ban Lists
    def add_to_watch(self, user_id: int, username: str) -> bool:
        """Add username to user's watch list"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        username = username.lower().strip('@')
        if username not in user['watch_list']:
            user['watch_list'].append(username)
            self.update_user(user_id, **user)
            
            # Initialize confirmation counter
            if username not in self.data['confirmation_counters']:
                self.data['confirmation_counters'][username] = {
                    'status': 'unknown',
                    'count': 0,
                    'last_check': None
                }
            self.save()
            return True
        return False
    
    def add_to_ban(self, user_id: int, username: str) -> bool:
        """Add username to user's ban list"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        username = username.lower().strip('@')
        if username not in user['ban_list']:
            user['ban_list'].append(username)
            self.update_user(user_id, **user)
            self.save()
            return True
        return True
    
    def remove_from_watch(self, user_id: int, username: str) -> bool:
        """Remove username from watch list"""
        user = self.get_user(user_id)
        if user and username in user['watch_list']:
            user['watch_list'].remove(username)
            self.update_user(user_id, **user)
            return True
        return False
    
    def remove_from_ban(self, user_id: int, username: str) -> bool:
        """Remove username from ban list"""
        user = self.get_user(user_id)
        if user and username in user['ban_list']:
            user['ban_list'].remove(username)
            self.update_user(user_id, **user)
            return True
        return False
    
    # Confirmation System
    def update_confirmation(self, username: str, status: str, count: int) -> Dict:
        """Update confirmation counter"""
        self.data['confirmation_counters'][username] = {
            'status': status,
            'count': count,
            'last_check': datetime.datetime.now().isoformat()
        }
        self.save()
        return self.data['confirmation_counters'][username]
    
    def get_confirmation(self, username: str) -> Dict:
        """Get confirmation counter"""
        return self.data['confirmation_counters'].get(username, {
            'status': 'unknown',
            'count': 0,
            'last_check': None
        })
    
    def reset_confirmation(self, username: str):
        """Reset confirmation counter"""
        self.update_confirmation(username, 'unknown', 0)
    
    # Subscription
    def is_subscription_active(self, user_id: int) -> bool:
        """Check if user has active subscription"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        if user['role'] in ['owner', 'admin']:
            return True
        
        expiry = user.get('subscription_expiry')
        if not expiry:
            return False
        
        try:
            expiry_date = datetime.datetime.fromisoformat(expiry)
            return expiry_date > datetime.datetime.now()
        except:
            return False
    
    def extend_subscription(self, user_id: int, days: int) -> bool:
        """Extend user subscription"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        now = datetime.datetime.now()
        if user.get('subscription_expiry'):
            try:
                current = datetime.datetime.fromisoformat(user['subscription_expiry'])
                if current > now:
                    new_expiry = current + datetime.timedelta(days=days)
                else:
                    new_expiry = now + datetime.timedelta(days=days)
            except:
                new_expiry = now + datetime.timedelta(days=days)
        else:
            new_expiry = now + datetime.timedelta(days=days)
        
        user['subscription_expiry'] = new_expiry.isoformat()
        self.update_user(user_id, **user)
        return True
    
    # Role Management
    def set_role(self, user_id: int, role: str) -> bool:
        """Set user role"""
        user = self.get_user(user_id)
        if user:
            user['role'] = role
            self.update_user(user_id, **user)
            return True
        return False
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        return list(self.data['users'].values())

# ============================================================================
# INSTAGRAM MONITORING ENGINE
# ============================================================================

class InstagramMonitor:
    """Instagram profile monitoring engine"""
    
    def __init__(self, db: DatabaseManager, bot_app: Application):
        self.db = db
        self.bot = bot_app.bot
        self.is_running = False
        self.session = None
    
    async def get_profile(self, username: str) -> InstagramProfile:
        """Fetch Instagram profile data"""
        try:
            # Using aiohttp for async requests
            if not self.session:
                self.session = aiohttp.ClientSession(headers=Config.INSTA_HEADERS)
            
            # Note: This is a simulation. In production, you'd use Instagram's API
            # For demo purposes, we'll simulate different responses
            
            # Simulate API call delay
            await asyncio.sleep(1)
            
            # Simulate different statuses based on username patterns
            username_lower = username.lower()
            
            # Simulate banned accounts
            if 'banned' in username_lower or 'suspended' in username_lower:
                return InstagramProfile(
                    username=username,
                    status=AccountStatus.BANNED
                )
            
            # Simulate active accounts
            profile = InstagramProfile(
                username=username,
                full_name=self._generate_full_name(username),
                followers=hash(username) % 100000,
                following=hash(username + 'f') % 1000,
                posts=hash(username + 'p') % 500,
                is_private='private' in username_lower,
                is_verified='verified' in username_lower,
                biography=f"Instagram user {username}",
                status=AccountStatus.ACTIVE
            )
            
            return profile
            
        except Exception as e:
            logging.error(f"Error fetching profile for {username}: {e}")
            return InstagramProfile(
                username=username,
                status=AccountStatus.UNKNOWN
            )
    
    def _generate_full_name(self, username: str) -> str:
        """Generate a simulated full name"""
        names = ["𝐀 ꜱ ᴍ ɪ 𝐓", "John Doe", "Jane Smith", "Alex Chen", "Maria Garcia"]
        import random
        return random.choice(names)
    
    async def check_usernames(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Collect all unique usernames to check
                all_usernames = set()
                users = self.db.get_all_users()
                
                for user in users:
                    all_usernames.update(user.get('watch_list', []))
                
                # Check each username
                for username in all_usernames:
                    try:
                        await self.check_single_username(username)
                    except Exception as e:
                        logging.error(f"Error checking {username}: {e}")
                    
                    # Small delay between checks to avoid rate limiting
                    await asyncio.sleep(2)
                
                # Update stats
                self.db.data['stats']['total_checks'] += len(all_usernames)
                self.db.save()
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
            
            # Wait for next check interval
            await asyncio.sleep(Config.CHECK_INTERVAL)
    
    async def check_single_username(self, username: str):
        """Check a single username with confirmation system"""
        profile = await self.get_profile(username)
        confirmation = self.db.get_confirmation(username)
        
        current_status = profile.status.value
        previous_status = confirmation['status']
        current_count = confirmation['count']
        
        # Update confirmation counter
        if current_status == previous_status and current_status != 'unknown':
            new_count = current_count + 1
        else:
            new_count = 1 if current_status != 'unknown' else 0
        
        self.db.update_confirmation(username, current_status, new_count)
        
        # Check if threshold reached
        if new_count >= Config.CONFIRMATION_THRESHOLD:
            await self.handle_status_change(username, profile, current_status)
            self.db.reset_confirmation(username)
    
    async def handle_status_change(self, username: str, profile: InstagramProfile, new_status: str):
        """Handle confirmed status change"""
        users = self.db.get_all_users()
        
        for user in users:
            user_id = user['user_id']
            
            # Check watch list -> banned
            if new_status == 'banned' and username in user.get('watch_list', []):
                # Move from watch to ban
                self.db.remove_from_watch(user_id, username)
                self.db.add_to_ban(user_id, username)
                await self.send_ban_alert(user_id, profile)
            
            # Check ban list -> active
            elif new_status == 'active' and username in user.get('ban_list', []):
                # Move from ban to watch
                self.db.remove_from_ban(user_id, username)
                self.db.add_to_watch(user_id, username)
                await self.send_unban_alert(user_id, profile)
    
    async def send_ban_alert(self, user_id: int, profile: InstagramProfile):
        """Send banned alert to user"""
        text = self._format_profile_alert(profile, "🚫 **ACCOUNT BANNED**")
        keyboard = [[
            InlineKeyboardButton("📊 Check Status", callback_data=f"status_{profile.username}"),
            InlineKeyboardButton("❌ Remove", callback_data=f"remove_{profile.username}")
        ]]
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            self.db.data['stats']['alerts_sent'] += 1
        except Exception as e:
            logging.error(f"Failed to send ban alert to {user_id}: {e}")
    
    async def send_unban_alert(self, user_id: int, profile: InstagramProfile):
        """Send unbanned alert to user"""
        text = self._format_profile_alert(profile, "✅ **ACCOUNT UNBANNED**")
        keyboard = [[
            InlineKeyboardButton("📊 Check Status", callback_data=f"status_{profile.username}"),
            InlineKeyboardButton("👀 Watch", callback_data=f"watch_{profile.username}")
        ]]
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            self.db.data['stats']['alerts_sent'] += 1
        except Exception as e:
            logging.error(f"Failed to send unban alert to {user_id}: {e}")
    
    def _format_profile_alert(self, profile: InstagramProfile, header: str) -> str:
        """Format profile alert message"""
        private_status = "🔒 Private" if profile.is_private else "🌐 Public"
        verified = "✅ Verified" if profile.is_verified else ""
        
        return f"""
{header}

━━━━━━━━━━━━━━━━━━━━━
**ACCOUNT DETAILS**
👤 **Name:** {profile.full_name}
📧 **Username:** @{profile.username}
👥 **Followers:** {profile.followers:,}
👤 **Following:** {profile.following:,}
📸 **Posts:** {profile.posts:,}
{private_status} {verified}

📝 **Bio:** {profile.biography[:100]}

🕐 Last Checked: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━

Powered by @proxyfxc | @proxydominates
"""

# ============================================================================
# FLASK KEEP-ALIVE SERVER
# ============================================================================

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'service': 'Instagram Monitor Bot',
        'channel': '@proxydominates',
        'developer': '@proxyfxc',
        'timestamp': datetime.datetime.now().isoformat()
    })

@flask_app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

def run_flask():
    """Run Flask server in a separate thread"""
    flask_app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))

# ============================================================================
# TELEGRAM BOT HANDLERS
# ============================================================================

class BotHandlers:
    """Main bot handlers class"""
    
    def __init__(self, db: DatabaseManager, monitor: InstagramMonitor):
        self.db = db
        self.monitor = monitor
    
    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================
    
    def _check_access(self, user_id: int, required_role: str = 'user') -> Tuple[bool, str]:
        """Check user access and subscription"""
        user = self.db.get_user(user_id)
        
        if not user:
            return False, "User not registered. Use /start to register."
        
        # Check role-based access
        if user['role'] == 'owner':
            return True, ""
        elif user['role'] == 'admin' and required_role in ['user', 'admin']:
            return True, ""
        elif required_role == 'admin':
            return False, "❌ Admin access required."
        
        # Check subscription for normal users
        