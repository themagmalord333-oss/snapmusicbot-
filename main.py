import os
import time
import threading
from flask import Flask
from instagrapi import Client

app = Flask(__name__)

# Ye variable humein screen par status dikhayega
bot_status = "⏳ Bot start ho raha hai..."

def run_bot():
    global bot_status
    cl = Client()
    
    USERNAME = "mag99mag99mag99" # Apna username yahan dalein
    PASSWORD = "9113380244" # Apna password yahan dalein
    
    try:
        bot_status = "🔄 Login karne ki koshish kar raha hoon..."
        print(bot_status)
        
        # Phone jaisa dikhne ke liye
        cl.set_user_agent("Instagram 219.0.0.12.117 Android (29/10; 480dpi; 1080x2202; Xiaomi; Redmi Note 9 Pro; joyeuse; qcom; en_US; 340011804)")
        
        cl.login(USERNAME, PASSWORD)
        bot_status = f"✅ LOGIN SUCCESS! Bot chal gaya (ID: {cl.user_id})"
        print(bot_status)
        
    except Exception as e:
        # Error ko pakad kar screen par dikhana
        bot_status = f"❌ LOGIN FAILED: {str(e)}. Instagram ne block kiya hai."
        print(bot_status)
        return

    TRIGGER = ".love"
    REPLY_TEXT = "❤️ Ye mera automated message hai! ❤️"
    processed_ids = set()

    while True:
        try:
            bot_status = "🟢 Bot Active hai aur '.love' ka wait kar raha hai!"
            messages = cl.direct_messages(amount=5)
            
            for msg in messages:
                if msg.id not in processed_ids:
                    if msg.user_id == cl.user_id and TRIGGER in msg.text.lower():
                        cl.direct_answer(msg.thread_id, REPLY_TEXT)
                        processed_ids.add(msg.id)
            
            time.sleep(10)
        except Exception as e:
            bot_status = f"⚠️ Loop mein error: {str(e)}"
            time.sleep(20)

@app.route('/')
def home():
    # Render ke URL par status dikhega
    return f"""
    <html>
        <body style="font-family: Arial; padding: 20px; background-color: #222; color: #fff;">
            <h2>Instagram Bot Status:</h2>
            <p style="font-size: 18px; padding: 15px; background: #333; border-radius: 8px;">{bot_status}</p>
            <p>Isko refresh karte raho status check karne ke liye.</p>
        </body>
    </html>
    """

if __name__ == "__main__":
    # Bot ko background mein chalana
    t = threading.Thread(target=run_bot)
    t.start()
    
    # Web server chalana
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
