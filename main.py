import instaloader
from instabot import Bot
import time
import os
import logging
import telebot
from telebot import types
import threading
import json
from datetime import datetime

# ==================== CONFIG ====================
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # @BotFather se lo
ALLOWED_USERS = [123456789, 987654321]  # Tumhara aur trusted logo ke Telegram IDs

# ==================== SETUP ====================
logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
instagram_bot = None
user_sessions = {}  # Telegram user ID -> Instagram username

# ==================== INSTAGRAM BOT CLASS ====================
class InstagramController:
    def __init__(self, telegram_id):
        self.telegram_id = telegram_id
        self.username = None
        self.password = None
        self.ig_bot = None
        self.ig_loader = None
        self.is_logged_in = False
        self.session_file = None
        
    def login(self, username, password):
        """Instagram mein login karo"""
        try:
            self.username = username
            self.password = password
            self.ig_bot = Bot()
            self.ig_loader = instaloader.Instaloader()
            
            # Session file check
            self.session_file = f"session_{username}.json"
            
            if os.path.exists(self.session_file):
                # Session se login
                self.ig_loader.load_session_from_file(username)
                self.ig_bot.login(username=username, use_cookie=True)
                send_telegram_message(self.telegram_id, "✅ **Session se login successful!**")
            else:
                # Password se login
                self.ig_loader.login(username, password)
                self.ig_loader.save_session_to_file()  # Session save
                self.ig_bot.login(username=username, password=password)
                
                # Session file rename karo
                if os.path.exists(f"{username}.session"):
                    os.rename(f"{username}.session", self.session_file)
                
                send_telegram_message(self.telegram_id, "✅ **Login successful! Session saved for next time.**")
            
            self.is_logged_in = True
            user_sessions[self.telegram_id] = self
            return True
            
        except Exception as e:
            send_telegram_message(self.telegram_id, f"❌ **Login failed:** `{str(e)}`")
            return False
    
    def send_messages(self, target, message, count):
        """Bulk messages bhejo"""
        if not self.is_logged_in:
            send_telegram_message(self.telegram_id, "❌ **Pehle login karo!**")
            return False
        
        try:
            # Target ka ID doondho
            user_id = self.ig_bot.get_user_id_from_username(target)
            
            msg = send_telegram_message(
                self.telegram_id, 
                f"📤 **Sending {count} messages to @{target}...**"
            )
            
            for i in range(count):
                try:
                    self.ig_bot.send_message(message, [user_id])
                    
                    # Progress update
                    if (i + 1) % 5 == 0:
                        edit_telegram_message(
                            self.telegram_id, 
                            msg.message_id,
                            f"📤 **Progress:** {i+1}/{count} messages sent to @{target}"
                        )
                    
                    # Smart delay
                    time.sleep(2)
                    
                    if (i + 1) % 10 == 0:
                        time.sleep(30)  # 30 sec break
                        
                except Exception as e:
                    send_telegram_message(
                        self.telegram_id, 
                        f"⚠️ **Error on message {i+1}:** `{str(e)}`"
                    )
                    time.sleep(5)
            
            send_telegram_message(
                self.telegram_id, 
                f"✅ **Successfully sent {count} messages to @{target}!**"
            )
            return True
            
        except Exception as e:
            send_telegram_message(
                self.telegram_id, 
                f"❌ **Failed to send messages:** `{str(e)}`"
            )
            return False
    
    def get_profile_info(self, username):
        """Profile info do"""
        try:
            profile = instaloader.Profile.from_username(self.ig_loader.context, username)
            info = f"""
📊 **Profile Info:** @{username}
━━━━━━━━━━━━━━━━━━━
👤 **Name:** {profile.full_name}
📝 **Bio:** {profile.biography}
🔗 **Link:** {profile.external_url}
👥 **Followers:** {profile.followers}
👣 **Following:** {profile.followees}
📸 **Posts:** {profile.mediacount}
🔒 **Private:** {'Yes' if profile.is_private else 'No'}
✅ **Verified:** {'Yes' if profile.is_verified else 'No'}
            """
            return info
        except Exception as e:
            return f"❌ Error: {e}"
    
    def logout(self):
        """Logout and clear session"""
        self.is_logged_in = False
        self.username = None
        self.password = None
        self.ig_bot = None
        self.ig_loader = None
        if self.telegram_id in user_sessions:
            del user_sessions[self.telegram_id]
        return True

# ==================== TELEGRAM HELPERS ====================
def send_telegram_message(chat_id, text, parse_mode='Markdown'):
    """Message bhejo"""
    return bot.send_message(chat_id, text, parse_mode=parse_mode)

def edit_telegram_message(chat_id, message_id, text, parse_mode='Markdown'):
    """Message edit karo"""
    bot.edit_message_text(text, chat_id, message_id, parse_mode=parse_mode)

def is_allowed_user(user_id):
    """Check if user is allowed"""
    return user_id in ALLOWED_USERS

# ==================== TELEGRAM COMMANDS ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    if not is_allowed_user(message.from_user.id):
        bot.reply_to(message, "❌ **Access Denied!**")
        return
    
    welcome = """
🤖 **Instagram Bot Controller**
━━━━━━━━━━━━━━━━━━━
✅ **Logged out**

**Available Commands:**
/login username password - Instagram login
/send target count message - Send messages
/info username - Get profile info
/followers username - Get followers list
/logout - Logout from Instagram
/status - Check login status
/help - Show this help

**Example:**
/login john_doe password123
/send priya_456 10 Hello
    """
    bot.reply_to(message, welcome, parse_mode='Markdown')

@bot.message_handler(commands=['login'])
def login_command(message):
    if not is_allowed_user(message.from_user.id):
        bot.reply_to(message, "❌ **Access Denied!**")
        return
    
    try:
        # Command format: /login username password
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "❌ **Usage:** `/login username password`", parse_mode='Markdown')
            return
        
        username = parts[1]
        password = parts[2]
        
        msg = bot.reply_to(message, f"🔄 **Logging in as @{username}...**")
        
        # Pehle logout karo agar already logged in hai
        if message.from_user.id in user_sessions:
            user_sessions[message.from_user.id].logout()
        
        # Naya Instagram controller banao
        controller = InstagramController(message.from_user.id)
        if controller.login(username, password):
            bot.edit_message_text(
                f"✅ **Login successful as @{username}!**", 
                message.chat.id, 
                msg.message_id,
                parse_mode='Markdown'
            )
        else:
            bot.edit_message_text(
                "❌ **Login failed!**", 
                message.chat.id, 
                msg.message_id,
                parse_mode='Markdown'
            )
            
    except Exception as e:
        bot.reply_to(message, f"❌ **Error:** `{str(e)}`", parse_mode='Markdown')

@bot.message_handler(commands=['send'])
def send_command(message):
    if not is_allowed_user(message.from_user.id):
        bot.reply_to(message, "❌ **Access Denied!**")
        return
    
    try:
        # Check if logged in
        if message.from_user.id not in user_sessions:
            bot.reply_to(message, "❌ **Pehle /login karo!**")
            return
        
        # Command format: /send target count message
        parts = message.text.split(maxsplit=3)
        if len(parts) < 4:
            bot.reply_to(message, "❌ **Usage:** `/send target count message`", parse_mode='Markdown')
            return
        
        target = parts[1]
        count = int(parts[2])
        msg_text = parts[3]
        
        controller = user_sessions[message.from_user.id]
        
        # Confirmation
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Yes", callback_data=f"send_yes:{target}:{count}:{msg_text}"),
            types.InlineKeyboardButton("❌ No", callback_data="send_no")
        )
        
        bot.reply_to(
            message, 
            f"📤 **Confirm Send**\n\n"
            f"**Target:** @{target}\n"
            f"**Count:** {count}\n"
            f"**Message:** {msg_text}\n\n"
            f"Proceed?",
            reply_markup=markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ **Error:** `{str(e)}`", parse_mode='Markdown')

@bot.message_handler(commands=['info'])
def info_command(message):
    if not is_allowed_user(message.from_user.id):
        bot.reply_to(message, "❌ **Access Denied!**")
        return
    
    try:
        if message.from_user.id not in user_sessions:
            bot.reply_to(message, "❌ **Pehle /login karo!**")
            return
        
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ **Usage:** `/info username`", parse_mode='Markdown')
            return
        
        username = parts[1]
        controller = user_sessions[message.from_user.id]
        
        msg = bot.reply_to(message, f"🔄 **Fetching info for @{username}...**")
        info = controller.get_profile_info(username)
        
        bot.edit_message_text(info, message.chat.id, msg.message_id, parse_mode='Markdown')
        
    except Exception as e:
        bot.reply_to(message, f"❌ **Error:** `{str(e)}`", parse_mode='Markdown')

@bot.message_handler(commands=['logout'])
def logout_command(message):
    if not is_allowed_user(message.from_user.id):
        bot.reply_to(message, "❌ **Access Denied!**")
        return
    
    if message.from_user.id in user_sessions:
        user_sessions[message.from_user.id].logout()
        bot.reply_to(message, "✅ **Logged out successfully!**")
    else:
        bot.reply_to(message, "❌ **Already logged out!**")

@bot.message_handler(commands=['status'])
def status_command(message):
    if not is_allowed_user(message.from_user.id):
        bot.reply_to(message, "❌ **Access Denied!**")
        return
    
    if message.from_user.id in user_sessions:
        controller = user_sessions[message.from_user.id]
        status = f"""
📊 **Status:** ✅ Logged In
👤 **User:** @{controller.username}
📁 **Session:** {'Available' if controller.session_file else 'New'}
        """
        bot.reply_to(message, status, parse_mode='Markdown')
    else:
        bot.reply_to(message, "📊 **Status:** ❌ Logged Out", parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    start_command(message)

# ==================== CALLBACK HANDLERS ====================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data.startswith('send_yes'):
        # Send confirmed
        parts = call.data.split(':', 3)
        target = parts[1]
        count = int(parts[2])
        msg_text = parts[3]
        
        controller = user_sessions.get(call.from_user.id)
        if controller:
            bot.edit_message_text(
                f"📤 **Sending to @{target}...**", 
                call.message.chat.id, 
                call.message.message_id,
                parse_mode='Markdown'
            )
            
            # Run in separate thread
            thread = threading.Thread(
                target=controller.send_messages, 
                args=(target, msg_text, count)
            )
            thread.start()
        else:
            bot.edit_message_text(
                "❌ **Session expired!**", 
                call.message.chat.id, 
                call.message.message_id,
                parse_mode='Markdown'
            )
            
    elif call.data == 'send_no':
        bot.edit_message_text(
            "❌ **Cancelled!**", 
            call.message.chat.id, 
            call.message.message_id,
            parse_mode='Markdown'
        )

# ==================== MAIN ====================
def main():
    print("🤖 Telegram Bot Started...")
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"Allowed Users: {ALLOWED_USERS}")
    
    # Create sessions directory
    if not os.path.exists('sessions'):
        os.makedirs('sessions')
    
    # Start bot
    bot.infinity_polling()

if __name__ == "__main__":
    main()