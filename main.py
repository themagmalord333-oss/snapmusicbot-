import os
import sys
import time
import traceback
from threading import Thread
from flask import Flask
from pyrogram import Client, filters
from pytgcalls import PyTgCalls

# ==========================================
# 🛑 ERROR LOGGING SYSTEM
# ==========================================
LOG_FILE = "error.log"

def log_error(msg):
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")
    print(msg, flush=True)

if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

# ==========================================
# 🌐 FLASK WEB SERVER (ERROR DISPLAY)
# ==========================================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            errors = f.read()
        if "FATAL CRASH" in errors:
            return f"<h1 style='color:red;'>Bot Crashed ❌</h1><h2>Asli Error Niche Likha Hai:</h2><pre style='background:#eee; padding:10px;'>{errors}</pre>"
    
    return "<h1 style='color:green;'>Bot Status: RUNNING ✅</h1><p>Gourisen OSINT Ghost Joiner is Live!</p>"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# Web server ko background mein start karo
Thread(target=run_web, daemon=True).start()

# ==========================================
# 🤖 BOT EXECUTION
# ==========================================
log_error("🚀 System Booting Up...")

try:
    API_ID = 37314366
    API_HASH = "bd4c934697e7e91942ac911a5a287b46"
    SESSION = "BQI5Xz4AVI4TqbArCsM9RzO-Gu7AB7Q0lwCrPOhy7XQe7gn4MDvjdtG_73ZUYqJimBDOvPVScQDBcAI9V64twfNiOe43KJYH8ZzR7XsTsnVwjT2C3hypDnEjo9JlDEoZwEC_DqQmL5e-s7hwVTn2hzuigEpmAuK7uxW8HODEOpanB16AAxN7dOb2WD5g3mrHKfZQfYy6bpf-77s757XB7YicVaG4zkiKDDAX0xDHR-wbNzGPGxETW4KbRtXI7CS5eCmrqpL05jV787w9DN06J-h1-LR4UlFwBFsAAXoeii7PqHkYfd5NKAnTuBb50t2dAYqMkRyp6UbPx_LuTgzAwkd0QGNXsAAAAAGc59H6AA"

    log_error("⏳ Initializing Pyrogram Client...")
    app = Client("GourisenGhost", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
    
    log_error("⏳ Initializing PyTgCalls...")
    call_py = PyTgCalls(app)

    @app.on_message(filters.command("join", prefixes=".") & filters.me)
    async def ghost_join(client, message):
        try:
            await call_py.join_group_call(message.chat.id)
            await message.edit("👻 **Gourisen OSINT: Joined VC!**")
        except Exception as e:
            await message.edit(f"❌ **Error:** `{e}`")

    @app.on_message(filters.command("leave", prefixes=".") & filters.me)
    async def ghost_leave(client, message):
        try:
            await call_py.leave_group_call(message.chat.id)
            await message.edit("👋 **Gourisen OSINT: Left VC.**")
        except Exception as e:
            await message.edit(f"❌ **Error:** `{e}`")

    log_error("✅ Start Command Sent to PyTgCalls. Bot is Live!")
    call_py.run()

except Exception as e:
    # Agar code crash hua, toh error file mein save ho jayega
    log_error("\n❌ FATAL CRASH:")
    log_error(traceback.format_exc())
    
    print("🛑 Error saved to webpage. Keeping server alive to show error...")
    # Render ko bewakoof banakar server on rakhna taaki aap error padh sakein
    time.sleep(3600)