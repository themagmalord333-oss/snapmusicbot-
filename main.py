import os
import asyncio
import random
import requests
from threading import Thread
from flask import Flask
from pyrogram import Client, filters
from instagrapi import Client as IGClient

# ==================== 🛑 LOOP CRASH FIX 🛑 ====================
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# ==============================================================

# ==================== CONFIGURATION ====================
API_ID = 37314366
API_HASH = "bd4c934697e7e91942ac911a5a287b46"
BOT_TOKEN = "8583883682:AAGpFqdU9roiAqv1FUbxr-gHVXTWmbmfkA"

# ==================== SERVER KEEP ALIVE ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "🔥 Session ID Bot is Running! 🔥"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ==================== BOT SETUP ====================
bot = Client("MagmaIG", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

ig_sessions = {}
is_spamming = {}

SPAM_MESSAGES = [
    "𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗜 𝗖𝗛𝗨𝗧 𝗠𝗘 𝗖𝗛𝗔𝗡𝗚𝗘𝗦 𝗖𝗢𝗠𝗠𝗜𝗧 𝗞𝗥𝗨𝗚𝗔 🤖🙏",
    "𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗞𝗜 𝗖𝗛𝗨𝗧 𝗞𝗢 𝗢𝗡𝗟𝗜𝗡𝗘 𝗢𝗟𝗫 𝗣𝗘 𝗕𝗘𝗖𝗛𝗨𝗡𝗚𝗔 💸",
    "𝗧𝗘𝗥𝗜 𝗦𝗛𝗔𝗞𝗔𝗟 𝗗𝗘𝗞𝗛 𝗞𝗘 𝗧𝗢 𝗦𝗨𝗔𝗥 𝗕𝗛𝗜 𝗨𝗟𝗧𝗜 𝗞𝗔𝗥 𝗗𝗘 🤮",
    "𝗦𝗬𝗦𝗧𝗘𝗠 𝗣𝗘 𝗦𝗬𝗦𝗧𝗘𝗠 𝗕𝗜𝗧𝗛𝗔 𝗗𝗘𝗡𝗚𝗘 𝗧𝗘𝗥𝗜 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘 🎛️"
]

# ==================== COMMANDS ====================
@bot.on_message(filters.command("start"))
async def start_cmd(c, m):
    await m.reply(
        "🔥 **IG SESSION SPAM BOT ONLINE!** 🔥\n\n"
        "Ab Password ki zaroorat nahi.\n"
        "Commands:\n"
        "1️⃣ `/login session_id_here`\n"
        "2️⃣ `/igspam target_username count`\n"
        "3️⃣ `/stop`"
    )

@bot.on_message(filters.command("login"))
async def login_cmd(c, m):
    if len(m.command) < 2: 
        return await m.reply("❌ Use: `/login <session_id>`")
    
    session_id = m.command[1]
    msg = await m.reply("🔄 Session ID bypass se login ho raha hai...")
    
    try:
        cl = IGClient()
        # Session ID se direct login
        cl.login_by_sessionid(session_id)
        
        ig_sessions[m.from_user.id] = cl
        await msg.edit("✅ **Login Successful (Bypassed Security)!**\nAb aap `/igspam` use kar sakte ho.")
    except Exception as e:
        await msg.edit(f"❌ Login Failed: {str(e)}")

@bot.on_message(filters.command("igspam"))
async def spam_cmd(c, m):
    uid = m.from_user.id
    if uid not in ig_sessions: return await m.reply("❌ Pehle `/login <session_id>` karo!")
    
    try: 
        target = m.command[1]
        count = int(m.command[2])
    except: 
        return await m.reply("❌ Use: `/igspam target_user 10`")
    
    cl = ig_sessions[uid]
    is_spamming[uid] = True
    await m.reply(f"🚀 Attacking `{target}`...")
    
    try:
        tid = cl.user_id_from_username(target)
        for i in range(count):
            if not is_spamming.get(uid): break
            cl.direct_send(random.choice(SPAM_MESSAGES), [tid])
            await asyncio.sleep(8)
        await m.reply("✅ Target Destroyed!")
    except Exception as e:
        await m.reply(f"❌ Error: {e}")
    finally:
        is_spamming[uid] = False

@bot.on_message(filters.command("stop"))
async def stop_cmd(c, m):
    is_spamming[m.from_user.id] = False
    await m.reply("🛑 Stopped.")

# ==================== EXECUTION ====================
if __name__ == "__main__":
    # Webhook cleanup (Just in case)
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    except: pass

    # Server Start
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
    
    # Bot Start
    print("🚀 Session Bot Starting...")
    bot.run()
