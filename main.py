import os
import asyncio
from threading import Thread
from flask import Flask
from pyrogram import Client, filters
from pytgcalls import PyTgCalls

# ==================== 🛑 RENDER LOOP FIX 🛑 ====================
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# ===============================================================

# --- WEB SERVER FOR RENDER ---
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "👻 Gourisen OSINT Ghost Joiner is Running! 👻"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port)

# --- BOT CONFIGURATION ---
API_ID = 37314366
API_HASH = "bd4c934697e7e91942ac911a5a287b46"
SESSION = "BQI5Xz4AVI4TqbArCsM9RzO-Gu7AB7Q0lwCrPOhy7XQe7gn4MDvjdtG_73ZUYqJimBDOvPVScQDBcAI9V64twfNiOe43KJYH8ZzR7XsTsnVwjT2C3hypDnEjo9JlDEoZwEC_DqQmL5e-s7hwVTn2hzuigEpmAuK7uxW8HODEOpanB16AAxN7dOb2WD5g3mrHKfZQfYy6bpf-77s757XB7YicVaG4zkiKDDAX0xDHR-wbNzGPGxETW4KbRtXI7CS5eCmrqpL05jV787w9DN06J-h1-LR4UlFwBFsAAXoeii7PqHkYfd5NKAnTuBb50t2dAYqMkRyp6UbPx_LuTgzAwkd0QGNXsAAAAAGc59H6AA"

app = Client("GhostBot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
call_py = PyTgCalls(app)

@app.on_message(filters.command("join", prefixes=".") & filters.me)
async def ghost_join(client, message):
    chat_id = message.chat.id
    try:
        if not call_py.active_calls:
            await call_py.start()
        await call_py.join_group_call(chat_id)
        await message.edit("👻 **Gourisen OSINT: Ghost Join Successful!**")
    except Exception as e:
        await message.edit(f"❌ **Error:** `{e}`")

@app.on_message(filters.command("leave", prefixes=".") & filters.me)
async def ghost_leave(client, message):
    try:
        await call_py.leave_group_call(message.chat.id)
        await message.edit("👋 **Gourisen OSINT: Left VC.**")
    except Exception as e:
        await message.edit(f"❌ **Error:** `{e}`")

if __name__ == "__main__":
    # Start Web Server
    Thread(target=run_web, daemon=True).start()
    
    # Start Bot
    print(">>> Gourisen OSINT GhostBot is running...")
    app.run()