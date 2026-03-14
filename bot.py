import os
import random
import time
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

captcha_answers = {}
captcha_attempts = {}

join_log = []
RAID_LIMIT = 10
RAID_WINDOW = 10

raid_locked = False
raid_unlock_time = 0


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

    buttons = []

    for x in options:
        buttons.append([InlineKeyboardButton(str(x), callback_data=f"captcha_{x}")])

    # silent honeypot button
    buttons.append([InlineKeyboardButton("I'm not a bot 🤖", callback_data="honeypot")])

    return f"What is {a} + {b} ?", answer, InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global raid_locked

    user = update.effective_user
    now = time.time()

    if raid_locked:
        if now < raid_unlock_time:
            await update.message.reply_text(
                "⚠️ Join system temporarily locked due to raid protection."
            )
            return
        else:
            raid_locked = False

    if user.id not in captcha_attempts:
        captcha_attempts[user.id] = []

    captcha_attempts[user.id] = [
        t for t in captcha_attempts[user.id] if now - t < 60
    ]

    if len(captcha_attempts[user.id]) >= 5:
        await update.message.reply_text("Too many attempts. Try again later.")
        return

    captcha_attempts[user.id].append(now)

    question, answer, keyboard = generate_math()

    captcha_answers[user.id] = answer

    await update.message.reply_text(
        f"Verify you are human:\n\n{question}",
        reply_markup=keyboard
    )


async def captcha_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user = query.from_user

    await query.answer()

    # honeypot trap
    if query.data == "honeypot":

        try:
            await context.bot.send_message(
                user.id,
                "🚫 Bot detected. Access blocked."
            )
        except:
            pass

        captcha_answers.pop(user.id, None)
        return

    if user.id not in captcha_answers:
        await query.edit_message_text("Captcha expired. Send /start again.")
        return

    chosen = int(query.data.split("_")[1])

    if chosen == captcha_answers[user.id]:

        expire = datetime.utcnow() + timedelta(seconds=5)

        invite = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            expire_date=expire,
            member_limit=1
        )

        await query.edit_message_text(
            "✅ Verification passed!\n\n"
            f"Join the group (link expires in 5 seconds):\n{invite.invite_link}"
        )

        captcha_answers.pop(user.id)

    else:
        await query.answer("Wrong answer.", show_alert=True)


async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global raid_locked, raid_unlock_time

    now = time.time()

    join_log.append(now)

    join_log[:] = [t for t in join_log if now - t < RAID_WINDOW]

    if len(join_log) >= RAID_LIMIT:

        raid_locked = True
        raid_unlock_time = now + 60

        await context.bot.send_message(
            GROUP_ID,
            "🚨 Raid detected. Join system locked for 60 seconds."
        )


async def delete_invite_links(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message

    if not message.text:
        return

    if "t.me/" in message.text or "telegram.me/" in message.text:

        try:
            await message.delete()
        except:
            pass


def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        CallbackQueryHandler(captcha_button)
    )

    app.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member)
    )

    app.add_handler(
        MessageHandler(filters.TEXT & filters.Chat(GROUP_ID), delete_invite_links)
    )

    print("Bot running...")

    app.run_polling()


if __name__ == "__main__":
    main()
