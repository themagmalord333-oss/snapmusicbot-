import os
import time
import threading
from flask import Flask
from instagrapi import Client

# --- Flask Web Server (Render ke liye zaroori) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running! Render is keeping me alive."

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- Main Instagram Bot Logic ---
def run_bot():
    cl = Client()
    
    # ⚠️ APNI DETAILS YAHAN DAALEIN ⚠️
    USERNAME = "magmaxrich"
    PASSWORD = "9113380244"
    SESSION_FILE = "52659413459%3A8GvKhj070iUqIQ%3A21%3AAYjEhhY2ZCJyKlZA-s937zNTRHtbNHqstCGhDG9dNQ"
    
    # 📝 APNA CUSTOM MESSAGE YAHAN SET KAREIN 📝
    # Pro Tip: Is message ke andar '.love' word mat likhna, warna bot baar-baar reply karta rahega (infinite loop).
    CUSTOM_REPLY = "❤️ Ye mera automated response hai. Swagat hai aapka! ❤️"

    print("Login process start ho raha hai...")
    try:
        if os.path.exists(SESSION_FILE):
            cl.load_settings(SESSION_FILE)
            cl.login(USERNAME, PASSWORD)
            print("✅ Purane Session se Login ho gaya!")
        else:
            cl.login(USERNAME, PASSWORD)
            cl.dump_settings(SESSION_FILE)
            print("✅ Naya Session ban gaya aur Login ho gaya!")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        print("Agar 'Challenge Required' aa raha hai, toh Instagram app mein ja kar 'This was me' par click karein.")
        return

    print("🤖 Bot Active Hai! '.love' trigger ka wait kar raha hoon...")

    while True:
        try:
            # Top 5 recent chats check karega
            threads = cl.get_threads(amount=5)
            
            for thread in threads:
                # Har thread ka sabse latest message nikalna
                messages = cl.direct_messages(thread.id, amount=1)
                if not messages:
                    continue
                
                last_msg = messages[0]

                # LOGIC FIX: Agar message AAPNE bheja hai AUR text mein kahin bhi '.love' hai
                if last_msg.user_id == cl.user_id and ".love" in last_msg.text.lower():
                    print(f"Trigger detected in thread: {thread.id}")
                    
                    # Custom message send karna
                    cl.direct_answer(thread.id, CUSTOM_REPLY)
                    print(f"✅ Auto-reply bhej diya gaya hai!")
                    
                    # Extra wait taaki ek hi message par double reply na ho
                    time.sleep(2)
            
            # Agli baar check karne se pehle 15 seconds ka delay (Ban hone se bachne ke liye)
            time.sleep(15)
            
        except Exception as e:
            print(f"⚠️ Polling Error: {e}")
            time.sleep(30) # Error aane par 30 sec rukna taaki account safe rahe

# --- Execution Start Here ---
if __name__ == "__main__":
    # Flask ko alag thread mein chalana taaki bot ruk na jaye
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Bot ko start karna
    run_bot()
