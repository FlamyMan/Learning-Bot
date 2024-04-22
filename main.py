from telegram.ext import Application
from bot import Bot
import os
from config import BOT_TOKEN

def bot_main():
    application: Application = Application.builder().token(BOT_TOKEN).build()
    application.add_handlers(Bot.HANDLERS)
    application.run_polling()

if __name__ == '__main__':
    bot_main()