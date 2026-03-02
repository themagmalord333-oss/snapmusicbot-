import os
import time
import threading
from flask import Flask
from instagrapi import Client

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running!"

def run_bot():
    cl = Client()
    # ⚠️ DETAILS DAALEIN
    USERNAME = "magmaxrich"
    PASSWORD = "9113380244"
    
    try:
        cl.login(USERNAME, PASSWORD)
        print("✅ Login Success!")
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return

    # Jis message ko trigger banana hai
    TRIGGER = ".love"
    REPLY_TEXT = "❤️ Ye mera automated response hai! ❤️"

    processed_messages = set() # Taaki ek hi message pe baar-baar reply na ho

    while True:
        try:
            # Apne inbox ke top 5 threads uthao
            threads = cl.get_threads(amount=5)
            
            for thread in threads:
                # Thread ke andar ke messages check karo
                messages = cl.direct_messages(thread.id, amount=3)
                
                for msg in messages:
                    # Agar message ID pehle process nahi hui hai
                    if msg.id not in processed_messages:
                        
                        # Check: Kya message AAPNE bheja hai aur usme '.love' hai?
                        if msg.user_id == cl.user_id and TRIGGER in msg.text.lower():
                            print(f"Match mil gaya! Thread: {thread.id}")
                            
                            # Reply bhejna
                            cl.direct_answer(thread.id, REPLY_TEXT)
                            print("✅ Reply sent!")
                            
                            # Is message ID ko 'done' list mein daal do
                            processed_messages.add(msg.id)
            
            time.sleep(10) # 10 seconds wait
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(20)

if __name__ == "__main__":
    t = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=os.environ.get("PORT", 8080)))
    t.start()
    run_bot()
