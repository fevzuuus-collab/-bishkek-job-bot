import os
import requests
from flask import Flask, request

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")
API = f"https://api.telegram.org/bot{TOKEN}"
states = {}

def send(chat_id, text, keyboard=None):
    data = {"chat_id": chat_id, "text": text}
    if keyboard:
        data["reply_markup"] = {
            "keyboard": keyboard,
            "resize_keyboard": True
        }
    return requests.post(f"{API}/sendMessage", json=data, timeout=15)

MENU = [
    [{"text": "🔎 Найти работу"}],
    [{"text": "📝 Разместить вакансию"}],
    [{"text": "📞 Связаться с администратором"}]
]
CANCEL = [[{"text": "❌ Отмена"}]]

@app.route("/")
def home():
    return "Bishkek Job Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    msg = data.get("message", {})
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = (msg.get("text") or "").strip()

    if not chat_id or not text or not TOKEN:
        return {"ok": True}

    if text.startswith("/start"):
        states.pop(chat_id, None)
        send(chat_id, "Привет! 👋 Это бот «Работа Бишкек».\nВыбери действие:", MENU)
        return {"ok": True}

    if text == "❌ Отмена":
        states.pop(chat_id, None)
        send(chat_id, "Заявка отменена.", MENU)
        return {"ok": True}

    if text == "🔎 Найти работу":
        send(chat_id, "Наш канал вакансий:\nhttps://t.me/bishkek_rabota_kgz", MENU)
        return {"ok": True}

    if text == "📞 Связаться с администратором":
        send(chat_id, "Напиши в канал: https://t.me/bishkek_rabota_kgz", MENU)
        return {"ok": True}

    if text == "📝 Разместить вакансию":
        states[chat_id] = {"step": 0, "answers": []}
        send(chat_id, "1/5. Какая должность?", CANCEL)
        return {"ok": True}

    state = states.get(chat_id)
    if state:
        state["answers"].append(text)
        state["step"] += 1
        prompts = [
            "2/5. Какая зарплата? Например, 25000 сом.",
            "3/5. Где находится работа?",
            "4/5. Телефон или Telegram работодателя?",
            "5/5. Опиши обязанности и график."
        ]

        if state["step"] < 5:
            send(chat_id, prompts[state["step"] - 1], CANCEL)
            return {"ok": True}

        title, salary, location, contact, details = state["answers"]
        application = (
            "🆕 Заявка на вакансию\n\n"
            f"💼 Должность: {title}\n"
            f"💰 Зарплата: {salary}\n"
            f"📍 Адрес: {location}\n"
            f"📞 Контакт: {contact}\n"
            f"📝 Условия: {details}\n"
            f"ID отправителя: {chat_id}"
        )

        if ADMIN_CHAT_ID:
            try:
                send(ADMIN_CHAT_ID, application).raise_for_status()
                send(chat_id, "Спасибо! Заявка отправлена на проверку.", MENU)
            except requests.RequestException:
                send(chat_id, "Не получилось отправить заявку администратору. Попробуй позже.", MENU)
        else:
            send(chat_id, "Заявка заполнена. Нужно ещё настроить ADMIN_CHAT_ID в Render.", MENU)

        states.pop(chat_id, None)
        return {"ok": True}

    send(chat_id, "Выбери действие в меню или отправь /start.", MENU)
    return {"ok": True}

@app.route("/check")
def check():
    if not TOKEN:
        return "BOT_TOKEN не настроен", 500
    r = requests.get(f"{API}/getMe", timeout=15)
    return r.text, r.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
