import os
import time
import threading
from flask import Flask
from instagrapi import Client

# --- Flask Server for Render ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running! Render is keeping me alive."

def run_flask():
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8080))

# --- Instagram Bot Logic ---
def run_bot():
    cl = Client()
    USERNAME = "YOUR_INSTAGRAM_USERNAME"
    PASSWORD = "YOUR_INSTAGRAM_PASSWORD"
    SESSION_FILE = "session.json"

    # Login Logic
    try:
        if os.path.exists(SESSION_FILE):
            cl.load_settings(SESSION_FILE)
            cl.login(USERNAME, PASSWORD)
            print("Logged in using Session File!")
        else:
            cl.login(USERNAME, PASSWORD)
            cl.dump_settings(SESSION_FILE)
            print("New Session File Created!")
    except Exception as e:
        print(f"Login Failed: {e}")
        return

    print("Bot is now monitoring DMs for '.love'...")

    while True:
        try:
            # Sirf unread ya top 5 threads check karein (Speed ke liye)
            threads = cl.get_threads(amount=5)
            
            for thread in threads:
                # Thread ke messages dekhein
                messages = cl.direct_messages(thread.id, amount=1)
                if not messages:
                    continue
                
                last_msg = messages[0]

                # Condition: Agar message MERA hai aur text '.love' hai
                if last_msg.user_id == cl.user_id and last_msg.text.lower() == ".love":
                    
                    # --- APNA MESSAGE YAHAN SET KAREIN ---
                    reply_text = "❤️ Swagat hai! Ye mera auto-reply message hai jo '.love' trigger par set kiya gaya hai. ❤️"
                    
                    cl.direct_answer(thread.id, reply_text)
                    print(f"Replied successfully to thread: {thread.id}")
            
            # 15 seconds ka wait (Rate limit se bachne ke liye)
            time.sleep(15)
            
        except Exception as e:
            print(f"Error while polling: {e}")
            time.sleep(30)

# --- Execute Everything ---
if __name__ == "__main__":
    # Flask ko background thread mein chalayein
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Bot ko main thread mein chalayein
    run_bot()
