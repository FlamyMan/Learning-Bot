import logging
from telegram.ext import Application, MessageHandler, filters, ConversationHandler, CommandHandler
from config import BOT_TOKEN

class BotStates():
    EXAM = "examine"


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING
)

logger = logging.getLogger(__name__)


async def start(update, context):
    await update.message.reply_text("Hello this bot doesn't work. Try Later.")

    return ConversationHandler.END

async def examine(update, context):
    await update.message.reply_text("Hello this command is currently WIP.")
    return BotStates.EXAM


async def stop(update, context):
    await update.message.reply_text("Have a good day!")
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('examine', examine)],

        states={
            BotStates.EXAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, examine)]
        },

        fallbacks=[CommandHandler('stop', stop)]
    )
    

    application.add_handler(conv_handler)
    

    application.run_polling()

if __name__ == '__main__':
    main()