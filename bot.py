import logging
from telegram import _update
from telegram.ext import MessageHandler, filters, ConversationHandler, CommandHandler, _callbackcontext
from get_info import get_info

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.NOTSET
)

logger = logging.getLogger(__name__)


class Bot():
    START = "start"
    EXAM = "examine"
    NEW_WORDS = "newword"
    GET_INFO = "getinfo"
    HELP = "help"
    STOP = "stop"
    CANCEL = "cancel"


    class BotStates():
        EXAM = "exam"
        NEW = "new word" 
        GET = "getword"


    class UserInfo():
        pass

    async def unknown_command(update: _update.Update, context: _callbackcontext.CallbackContext):
        if update.message.text[1:] not in Bot.COMMANDS.keys():
            #await update.message.reply_text(f"I don't know the command {update.message.text}")
            await update.message.reply_text('\n'.join([str(h) for h in Bot.HANDLERS]))

    async def help(update: _update.Update, context: _callbackcontext.CallbackContext):
        with open("help_text.txt") as f:
            text = f.read()
        await update.message.reply_text(text)

    async def start(update: _update.Update, context: _callbackcontext.CallbackContext):
        await update.message.reply_text("Hello this bot doesn't work yet. Try Later.")

    async def new_word(update: _update.Update, context: _callbackcontext.CallbackContext):
        await update.message.reply_text("Hello this command is currently WIP." + f"Command name {Bot.NEW_WORDS}")

    async def get_info_command(update: _update.Update, context: _callbackcontext.CallbackContext):
        await update.message.reply_text("Please write the word you need.")
        return Bot.BotStates.GET

    async def examine(update: _update.Update, context: _callbackcontext.CallbackContext):
        await update.message.reply_text("Hello this command is currently WIP." + f"Command name {Bot.EXAM}")
        return ConversationHandler.END

    async def cancel(update: _update.Update, context: _callbackcontext.CallbackContext):
        await update.message.reply_text("Action canceled!")
        return ConversationHandler.END
    
    async def stop(update: _update.Update, context: _callbackcontext.CallbackContext):
        await update.message.reply_text("Have a good day!")
        return ConversationHandler.END
    
    async def get_info(update: _update.Update, context: _callbackcontext.CallbackContext):
        await update.message.reply_text(get_info.generate_bot_answer(update.message.text))
        return ConversationHandler.END

    UNKNOWN_COMMAND = MessageHandler(filters.COMMAND, unknown_command)

    COMMANDS = {
        START: CommandHandler(START, start),
        EXAM: CommandHandler(EXAM, examine),
        NEW_WORDS: CommandHandler(NEW_WORDS, new_word),
        GET_INFO: CommandHandler(GET_INFO, get_info_command),
        STOP: CommandHandler(STOP, stop),
        CANCEL: CommandHandler(CANCEL, cancel),
        HELP: CommandHandler(HELP, help)
    }

    ExamHandler = ConversationHandler(
            entry_points=[COMMANDS[EXAM]],

            states={
                BotStates.EXAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, examine)]
            },

            fallbacks=[COMMANDS[STOP]]
        )
    
    INFO_HANDLER = ConversationHandler(
        entry_points=[COMMANDS[GET_INFO]],
        states={
            BotStates.GET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_info)]
        },
        fallbacks=[COMMANDS[STOP], COMMANDS[CANCEL]]
    )
    # UNKNOWN COMMAND MUST BE AT THE END OF THIS LIST
    HANDLERS =list(COMMANDS.values()) + [ExamHandler, UNKNOWN_COMMAND]


