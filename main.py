from telegram.ext import Application
from bot import Bot
import server
from config import BOT_TOKEN
import asyncio

def bot_main():
    application: Application = Application.builder().token(BOT_TOKEN).build()
    application.add_handlers(Bot.HANDLERS)
    application.run_polling()

if __name__ == '__main__':
    bot_main()