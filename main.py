import os
import json
import threading
from flask import Flask
from instagrapi import Client

app = Flask(__name__)

# Web page par dikhane ke liye variable
session_result = "⏳ Session ban raha hai... Thoda wait karein aur page ko 30 second baad refresh karein."

def generate_session():
    global session_result
    cl = Client()
    
    # ⚠️ APNI DETAILS YAHAN DAALEIN
    USERNAME = "mag99mag99mag99"
    PASSWORD = "9113380244"
    
    try:
        print("Login attempt start...")
        cl.set_user_agent("Instagram 219.0.0.12.117 Android (29/10; 480dpi; 1080x2202; Xiaomi; Redmi Note 9 Pro; joyeuse; qcom; en_US; 340011804)")
        
        cl.login(USERNAME, PASSWORD)
        
        # Session ka data nikalna
        session_data = cl.get_settings()
        
        # Data ko sundar JSON format mein badalna
        session_result = json.dumps(session_data, indent=4)
        print("✅ Session ban gaya!")
        
    except Exception as e:
        # Agar block hua toh error screen par dikhega
        session_result = f"❌ ERROR AA GAYA:\n\n{str(e)}\n\n(Bhai, Render ka IP sach mein block hai. Humein kisi dusri jagah se session banana padega.)"
        print("❌ Login Failed.")

@app.route('/')
def home():
    # Web page ka design jo aapko data dikhayega
    return f"""
    <html>
        <body style="font-family: monospace; background-color: #121212; color: #00ff00; padding: 20px;">
            <h2>Instagram Session Data:</h2>
            <pre style="background: #000; padding: 15px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;">{session_result}</pre>
            <p style="color: white; font-family: Arial;"><b>Instruction:</b> Agar upar bohot saara code (JSON) aa gaya hai, toh us pure text ko copy karo aur apne GitHub mein 'session_insta.json' naam ki file banakar paste kar do.</p>
        </body>
    </html>
    """

if __name__ == "__main__":
    # Background mein login process chalana
    t = threading.Thread(target=generate_session)
    t.start()
    
    # Render ka web server on karna
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
