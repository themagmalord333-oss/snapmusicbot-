import os
import time
import threading
from flask import Flask
from instagrapi import Client

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Active and Running!"

def run_bot():
    cl = Client()
    # ⚠️ APNI DETAILS DAALEIN
    USERNAME = "magmaxrich"
    PASSWORD = "9113380244"
    
    try:
        # Session handle karne ke liye simple login
        cl.login(USERNAME, PASSWORD)
        print(f"✅ Login Success for: {USERNAME}")
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return

    TRIGGER = ".love"
    REPLY_TEXT = "❤️ Ye mera automated response hai! ❤️"
    
    # Taaki ek hi message pe baar-baar reply na ho
    last_processed_msg_id = None

    print("🤖 Monitoring started... Send '.love' in any DM.")

    while True:
        try:
            # Apne bheje gaye aakhri 5 messages check karein
            # Ye specifically AAPKE messages ko scan karega
            my_messages = cl.direct_messages(amount=5)
            
            for msg in my_messages:
                # Agar message naya hai aur usme trigger word hai
                if msg.id != last_processed_msg_id:
                    if msg.user_id == cl.user_id and TRIGGER in msg.text.lower():
                        print(f"🎯 Trigger found in Thread: {msg.thread_id}")
                        
                        # Reply bhejna
                        cl.direct_answer(msg.thread_id, REPLY_TEXT)
                        print("✅ Auto-reply sent successfully!")
                        
                        # ID save karlo taaki repeat na ho
                        last_processed_msg_id = msg.id
                        break # Ek baar mein ek hi process karein
            
            time.sleep(10) # 10 seconds ka gap rakhein
            
        except Exception as e:
            print(f"⚠️ Loop Error: {e}")
            time.sleep(20)

if __name__ == "__main__":
    # Flask for Render
    port = int(os.environ.get("PORT", 8080))
    t = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port))
    t.start()
    
    # Start Bot
    run_bot()
