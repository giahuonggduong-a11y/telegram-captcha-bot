import os
import random
import time
import asyncio
import requests
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

PORT = int(os.getenv("PORT", 8080))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

captcha_sessions = {}
captcha_attempts = {}
blocked_users = {}

COOLDOWN_TIME = 60


def generate_math():

    a = random.randint(1, 10)
    b = random.randint(1, 10)
    answer = a + b

    options = [answer]

    while len(options) < 3:
        wrong = answer + random.randint(-5, 5)
        if wrong != answer and wrong > 0:
            options.append(wrong)

    random.shuffle(options)

    keyboard = []

    for x in options:
        keyboard.append(
            [InlineKeyboardButton(str(x), callback_data=f"captcha_{x}")]
        )

    keyboard.append(
        [InlineKeyboardButton("🤖", callback_data="honeypot")]
    )

    return f"What is {a} + {b} ?", answer, InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    now = time.time()

    # ignore if user is blocked
    if user.id in blocked_users:

        if now < blocked_users[user.id]:
            return
        else:
            blocked_users.pop(user.id)

    if user.id not in captcha_attempts:
        captcha_attempts[user.id] = []

    captcha_attempts[user.id] = [
        t for t in captcha_attempts[user.id] if now - t < 60
    ]

    if len(captcha_attempts[user.id]) >= 5:

        blocked_users[user.id] = now + COOLDOWN_TIME

        await update.message.reply_text(
            "Too many attempts. Please try again later."
        )

        return

    captcha_attempts[user.id].append(now)

    question, answer, keyboard = generate_math()

    captcha_sessions[user.id] = {
        "answer": answer,
        "created": now
    }

    await update.message.reply_text(
        f"Verify you are human:\n\n{question}",
        reply_markup=keyboard
    )


async def captcha_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user = query.from_user

    await query.answer()

    if query.data == "honeypot":

        captcha_sessions.pop(user.id, None)

        try:
            await context.bot.send_message(
                user.id,
                "🚫 Bot detected. Access blocked."
            )
        except:
            pass

        return

    if user.id not in captcha_sessions:
        await query.edit_message_text("Captcha expired. Send /start again.")
        return

    chosen = int(query.data.split("_")[1])
    correct = captcha_sessions[user.id]["answer"]

    if chosen == correct:

        expire = datetime.utcnow() + timedelta(seconds=5)

        invite = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            expire_date=expire,
            member_limit=1
        )

        msg = await query.edit_message_text(
            "✅ Verification passed!\n\n"
            f"Join the group here (link expires in 5 seconds):\n{invite.invite_link}"
        )

        captcha_sessions.pop(user.id)

        context.application.create_task(
            delete_invite_message(context, user.id, msg.message_id)
        )

    else:

        await query.answer("Wrong answer.", show_alert=True)


async def delete_invite_message(context, user_id, message_id):

    await asyncio.sleep(5)

    try:

        await context.bot.delete_message(
            chat_id=user_id,
            message_id=message_id
        )

        await context.bot.send_message(
            chat_id=user_id,
            text="⏱ The invite link expired. Please send /start to try again."
        )

    except:
        pass


def fix_webhook():

    if not WEBHOOK_URL:
        return False

    try:

        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        info = requests.get(url).json()

        current = info["result"]["url"]

        if current != WEBHOOK_URL:

            set_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"
            requests.get(set_url)

        return True

    except:
        return False


def main():

    print("Starting bot...")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(captcha_button))

    webhook_ok = fix_webhook()

    if webhook_ok and WEBHOOK_URL:

        print("Running in WEBHOOK mode")

        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL
        )

    else:

        print("Webhook failed. Switching to POLLING mode")

        app.run_polling()


if __name__ == "__main__":
    main()
