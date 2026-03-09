# Telegram Captcha Bot

1-file Telegram bot with math captcha buttons that auto deletes messages and shows retry.

## Deploy to Railway

Click the button below to deploy to Railway:

[![Deploy to Railway](https://railway.app/button.svg)](https://railway.app/new/project?template=https://github.com/giahuonggduong-a11y/telegram-captcha-bot)

## Environment Variables

Add the following variable in Railway:

## Keep 24/7 Online

1. Go to [UptimeRobot](https://uptimerobot.com/)  
2. Create a **New HTTP Monitor**  
   - URL: `https://your-railway-project.up.railway.app/`  
   - Method: GET  
   - Interval: 5 minutes  

This keeps the Railway free dyno awake 24/7.

## Usage

- `/start` → sends a math captcha
- Tap the correct answer
- Correct → shows message for 5 sec then disappears
- Wrong → new captcha
