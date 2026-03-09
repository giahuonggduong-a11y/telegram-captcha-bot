import random
import asyncio
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
CUSTOM_MESSAGE = "✅ You passed the captcha, join the channel http://t.me/+_-kLSN2ul783Yjg0"
answers = {}

def captcha():
    a = random.randint(1,10)
    b = random.randint(1,10)
    correct = a + b
    options = [correct]
    while len(options) < 4:
        x = correct + random.randint(-5,5)
        if x > 0 and x not in options:
            options.append(x)
    random.shuffle(options)
    return f"{a} + {b}", correct, options

async def send_captcha(chat_id, context):
    q, correct, options = captcha()
    answers[chat_id] = correct
    keyboard = [[InlineKeyboardButton(str(o), callback_data=str(o))] for o in options]
    await context.bot.send_message(chat_id, f"Solve captcha:\n\n{q} = ?", reply_markup=InlineKeyboardMarkup(keyboard))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_captcha(update.effective_chat.id, context)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat = query.message.chat.id
    selected = int(query.data)
    correct = answers.get(chat)

    if selected != correct:
        await query.edit_message_text("❌ Wrong answer. Try again.")
        await send_captcha(chat, context)
        return

    msg = await context.bot.send_message(chat, CUSTOM_MESSAGE)
    await asyncio.sleep(5)
    try:
        await msg.delete()
    except:
        pass
    await context.bot.send_message(chat, "⏰ Time ran out. Retry captcha.")
    await send_captcha(chat, context)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("Bot running...")
app.run_polling()
