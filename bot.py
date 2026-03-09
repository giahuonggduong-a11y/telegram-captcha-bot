import os
import random
import asyncio
from threading import Thread
from flask import Flask
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ---------------- Logging ----------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ---------------- Configuration ----------------
TOKEN = os.getenv("TOKEN")  # Set TOKEN in Railway environment variables
CUSTOM_MESSAGE = "✅ You passed the captcha, join the channel http://t.me/+_-kLSN2ul783Yjg0"
answers = {}

# ------------- Captcha Functions ----------------
def captcha():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    correct = a + b
    options = [correct]
    while len(options) < 4:
        x = correct + random.randint(-5, 5)
        if x > 0 and x not in options:
            options.append(x)
    random.shuffle(options)
    return f"{a} + {b}", correct, options

async def send_captcha(chat_id, context):
    q, correct, options = captcha()
    answers[chat_id] = correct
    keyboard = [[InlineKeyboardButton(str(o), callback_data=str(o))] for o in options]
    logger.info(f"Sending captcha to chat {chat_id}: {q} = {correct}")
    await context.bot.send_message(chat_id, f"Solve captcha:\n\n{q} = ?", reply_markup=InlineKeyboardMarkup(keyboard))

# ------------- Bot Handlers ----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    logger.info(f"/start received from user {user.username} ({user.id}) in chat {chat_id}")
    await send_captcha(chat_id, context)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat = query.message.chat.id
    user = query.from_user.username
    selected = int(query.data)
    correct = answers.get(chat)

    logger.info(f"User {user} in chat {chat} pressed button {selected} (correct: {correct})")

    if selected != correct:
        await query.edit_message_text("❌ Wrong answer. Try again.")
        await send_captcha(chat, context)
        return

    msg = await context.bot.send_message(chat, CUSTOM_MESSAGE)
    await asyncio.sleep(5)
    try:
        await msg.delete()
        logger.info(f"Deleted success message in chat {chat}")
    except:
        logger.warning(f"Failed to delete success message in chat {chat}")
    await context.bot.send_message(chat, "⏰ Time ran out. Retry captcha.")
    await send_captcha(chat, context)

# ------------- Flask Keep-Alive ------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)

# ------------- Run Bot --------------------------
def run_bot():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    logger.info("Bot is running...")
    application.run_polling()

# ------------- Start both -----------------------
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    run_bot()
