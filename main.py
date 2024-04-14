from telegram.ext import Application
from bot import Bot
from config import BOT_TOKEN


def main():
    application: Application = Application.builder().token(BOT_TOKEN).build()
    application.add_handlers(Bot.HANDLERS)
    application.run_polling()

if __name__ == '__main__':
    main()