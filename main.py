import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")

@app.route("/", methods=["GET"])
def home():
    return "Bishkek Job Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    message = data.get("message", {})
    chat = message.get("chat", {})
    text = message.get("text", "")
    chat_id = chat.get("id")

    if chat_id and text == "/start":
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": (
                    "Привет! 👋 Это бот «Работа Бишкек».\n\n"
                    "Здесь можно будет разместить вакансию.\n"
                    "Скоро добавим приём заявок!"
                )
            },
            timeout=15
        )

    return {"ok": True}

@app.route("/check", methods=["GET"])
def check():
    if not TOKEN:
        return "BOT_TOKEN не настроен", 500

    r = requests.get(
        f"https://api.telegram.org/bot{TOKEN}/getMe",
        timeout=15
    )
    return r.text, r.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
