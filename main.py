import os
import requests
from flask import Flask

app = Flask(name)

TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL = os.environ.get("CHANNEL_ID", "@bishkek_rabota_kgz")

@app.route("/")
def home():
return "Bishkek Job Bot is running!"

@app.route("/check")
def check():
if not TOKEN:
return "BOT_TOKEN is not configured", 500
r = requests.get(
f"https://api.telegram.org/bot{TOKEN}/getMe",
timeout=15
)
return r.text, r.status_code

if name == "main":
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
