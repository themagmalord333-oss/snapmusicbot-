import os
import asyncio
from threading import Thread
from flask import Flask
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls

# ==========================================
# 🌐 FLASK WEB SERVER (TO KEEP RENDER ALIVE)
# ==========================================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "👻 Gourisen OSINT: Ghost Joiner is Live and Running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ==========================================
# 🤖 BOT CONFIGURATION 
# ==========================================
API_ID = 37314366
API_HASH = "bd4c934697e7e91942ac911a5a287b46"
SESSION = "BQI5Xz4AVI4TqbArCsM9RzO-Gu7AB7Q0lwCrPOhy7XQe7gn4MDvjdtG_73ZUYqJimBDOvPVScQDBcAI9V64twfNiOe43KJYH8ZzR7XsTsnVwjT2C3hypDnEjo9JlDEoZwEC_DqQmL5e-s7hwVTn2hzuigEpmAuK7uxW8HODEOpanB16AAxN7dOb2WD5g3mrHKfZQfYy6bpf-77s757XB7YicVaG4zkiKDDAX0xDHR-wbNzGPGxETW4KbRtXI7CS5eCmrqpL05jV787w9DN06J-h1-LR4UlFwBFsAAXoeii7PqHkYfd5NKAnTuBb50t2dAYqMkRyp6UbPx_LuTgzAwkd0QGNXsAAAAAGc59H6AA"

app = Client("GourisenGhost", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(app)

# ==========================================
# 🛠️ COMMAND HANDLERS
# ==========================================
@app.on_message(filters.command("join", prefixes=".") & filters.me)
async def ghost_join(client, message):
    try:
        chat_id = message.chat.id
        await call_py.join_group_call(chat_id)
        await message.edit("👻 **Gourisen OSINT: Joined VC Successfully!**")
    except Exception as e:
        await message.edit(f"❌ **Join Error:** `{e}`")

@app.on_message(filters.command("leave", prefixes=".") & filters.me)
async def ghost_leave(client, message):
    try:
        chat_id = message.chat.id
        await call_py.leave_group_call(chat_id)
        await message.edit("👋 **Gourisen OSINT: Left VC.**")
    except Exception as e:
        await message.edit(f"❌ **Leave Error:** `{e}`")

# ==========================================
# 🚀 MAIN ASYNC EXECUTION (PYTHON 3.14 SAFE)
# ==========================================
async def main():
    print("🚀 Starting Gourisen OSINT Userbot...")
    try:
        await app.start()
        await call_py.start()
        print("✅ Gourisen OSINT is Online! Send .join in any group.")
        await idle()
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    # 1. Start Web Server in a separate thread
    Thread(target=run_web, daemon=True).start()
    
    # 2. Start Bot using asyncio.run() to strictly avoid loop errors
    try:
        asyncio.run(main())
    except Exception as crash_error:
        print(f"🛑 Server Crash Prevented: {crash_error}")