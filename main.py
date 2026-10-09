import os
import uuid
import requests
from flask import Flask, request

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_CHAT_ID = str(os.environ.get("ADMIN_CHAT_ID", ""))
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@bishkek_rabota_kgz")
API = f"https://api.telegram.org/bot{TOKEN}"

states = {}
pending = {}

MENU = {
    "keyboard": [
        [{"text": "🔎 Найти работу"}],
        [{"text": "📝 Разместить вакансию"}],
        [{"text": "📞 Связаться с администратором"}]
    ],
    "resize_keyboard": True
}
CANCEL = {
    "keyboard": [[{"text": "❌ Отмена"}]],
    "resize_keyboard": True
}

def send(chat_id, text, keyboard=None):
    data = {"chat_id": chat_id, "text": text}
    if keyboard:
        data["reply_markup"] = keyboard
    return requests.post(
        f"{API}/sendMessage", json=data, timeout=15
    )

@app.route("/")
def home():
    return "Bishkek Job Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    # Обработка кнопок модерации
    callback = data.get("callback_query")
    if callback:
        callback_id = callback.get("id")
        user_id = str(callback.get("from", {}).get("id", ""))
        msg = callback.get("message", {})
        admin_chat = str(msg.get("chat", {}).get("id", ""))
        message_id = msg.get("message_id")
        action = callback.get("data", "")

        if user_id != ADMIN_CHAT_ID or admin_chat != ADMIN_CHAT_ID:
            requests.post(
                f"{API}/answerCallbackQuery",
                json={
                    "callback_query_id": callback_id,
                    "text": "Эта кнопка доступна только администратору."
                },
                timeout=15
            )
            return {"ok": True}

        parts = action.split(":", 1)
        if len(parts) != 2 or parts[1] not in pending:
            requests.post(
                f"{API}/answerCallbackQuery",
                json={
                    "callback_query_id": callback_id,
                    "text": "Заявка уже обработана или устарела."
                },
                timeout=15
            )
            return {"ok": True}

        decision, job_id = parts
        job = pending[job_id]

        if decision == "approve":
            try:
                result = requests.post(
                    f"{API}/sendMessage",
                    json={
                        "chat_id": CHANNEL_ID,
                        "text": job["post"]
                    },
                    timeout=15
                )
                result.raise_for_status()
                if not result.json().get("ok"):
                    raise RuntimeError("Telegram не опубликовал сообщение")

                send(ADMIN_CHAT_ID, "✅ Вакансия опубликована в канале.")
                send(
                    job["user_id"],
                    "✅ Твоя вакансия одобрена и опубликована!",
                    MENU
                )
            except Exception:
                send(
                    ADMIN_CHAT_ID,
                    "Не удалось опубликовать вакансию. Проверь права бота в канале и переменную CHANNEL_ID."
                )
                return {"ok": True}

        elif decision == "reject":
            send(ADMIN_CHAT_ID, "❌ Заявка отклонена.")
            send(
                job["user_id"],
                "❌ К сожалению, вакансия не прошла проверку.",
                MENU
            )
        else:
            return {"ok": True}

        pending.pop(job_id, None)
        requests.post(
            f"{API}/editMessageReplyMarkup",
            json={
                "chat_id": ADMIN_CHAT_ID,
                "message_id": message_id,
                "reply_markup": {"inline_keyboard": []}
            },
            timeout=15
        )
        requests.post(
            f"{API}/answerCallbackQuery",
            json={"callback_query_id": callback_id, "text": "Готово"},
            timeout=15
        )
        return {"ok": True}

    msg = data.get("message", {})
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = (msg.get("text") or "").strip()

    if not chat_id or not text or not TOKEN:
        return {"ok": True}

    if text.startswith("/start"):
        states.pop(chat_id, None)
        send(
            chat_id,
            "Привет! 👋 Это бот «Работа Бишкек».\nВыбери действие:",
            MENU
        )
        return {"ok": True}

    if text == "❌ Отмена":
        states.pop(chat_id, None)
        send(chat_id, "Заявка отменена.", MENU)
        return {"ok": True}

    if text == "🔎 Найти работу":
        send(
            chat_id,
            "Наш канал вакансий:\nhttps://t.me/bishkek_rabota_kgz",
            MENU
        )
        return {"ok": True}

    if text == "📞 Связаться с администратором":
    send(
        chat_id,
        "📩 Связаться с администратором:\nhttps://t.me/Shidolino",
        MENU
    )
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

        post_text = (
            "💼 ВАКАНСИЯ\n\n"
            f"👔 Должность: {title}\n"
            f"💰 Зарплата: {salary}\n"
            f"📍 Адрес: {location}\n"
            f"📞 Контакт: {contact}\n"
            f"📝 Условия: {details}\n\n"
            "📩 Откликайтесь напрямую работодателю."
        )

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
            job_id = uuid.uuid4().hex[:12]
            pending[job_id] = {
                "post": post_text,
                "user_id": chat_id
            }
            keyboard = {
                "inline_keyboard": [[
                    {
                        "text": "✅ Опубликовать",
                        "callback_data": f"approve:{job_id}"
                    },
                    {
                        "text": "❌ Отклонить",
                        "callback_data": f"reject:{job_id}"
                    }
                ]]
            }

            try:
                result = send(ADMIN_CHAT_ID, application, keyboard)
                result.raise_for_status()
                if not result.json().get("ok"):
                    raise RuntimeError("Не удалось отправить заявку")
                send(
                    chat_id,
                    "Спасибо! Заявка отправлена на проверку.",
                    MENU
                )
            except Exception:
                pending.pop(job_id, None)
                send(
                    chat_id,
                    "Не удалось отправить заявку администратору. Попробуй позже.",
                    MENU
                )
        else:
            send(
                chat_id,
                "Не настроен ADMIN_CHAT_ID в Render.",
                MENU
            )

        states.pop(chat_id, None)
        return {"ok": True}

    send(chat_id, "Выбери действие в меню или отправь /start.", MENU)
    return {"ok": True}

@app.route("/check")
def check():
    if not TOKEN:
        return "BOT_TOKEN не настроен", 500
    result = requests.get(f"{API}/getMe", timeout=15)
    return result.text, result.status_code

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
        )
