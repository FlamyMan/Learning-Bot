import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import MessageHandler, filters, ConversationHandler, CommandHandler, ContextTypes, CallbackQueryHandler
from server import get_info

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class Bot():
    START = "start"
    EXAM = "exam"
    NEW_WORDS = "newwords"
    GET_INFO = "getinfo"
    HELP = "help"
    STOP = "stop"
    CANCEL = "cancel"
    SETTINGS = "SETTINGS"


    class States():
        EXAM = "exam"
        NEW = "new word" 
        GET = "getword"


    class UserDataKeys():
        SETTINGS = "SETTINGS"
        WORDS = "WORDS"
        LEVEL = "LEVEL"
         
        EXAM_TYPE = "EXAM_TYPE" 

        NECECERALY_KEYS = [WORDS, LEVEL, SETTINGS]

        DEFAULT_VALUES = {
            WORDS: [],
            LEVEL: 5,
            SETTINGS: { #todo: create settings
                "": ""
            }
        }
    
    class CallbackWorker:
        SETTINGS_HELLO = "hello"
        async def on_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            await query.answer()

            await query.edit_message_text(query.data)

    async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"I don't know the command {update.message.text}")

    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        with open("help_text.txt") as f:
            text = f.read()
        await update.message.reply_text(text)

    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not len([k for k in context.user_data.keys() if k in Bot.UserDataKeys.NECECERALY_KEYS]) == len(Bot.UserDataKeys.NECECERALY_KEYS):
            for key in Bot.UserDataKeys.NECECERALY_KEYS:
                context.user_data[key] = Bot.UserDataKeys.DEFAULT_VALUES[key]

            await update.message.reply_text(f"こんにちは{update.effective_sender.full_name}さん！")
            await Bot.help(update, context)
        else:
            await update.message.reply_text(f"Hmm... It seems like you have already started.")

    async def new_words_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("This command is currently WIP. " + f"Command name {Bot.NEW_WORDS}")

    async def get_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Please specify the word you are interested in.")
        return Bot.States.GET

    async def exam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("This command is currently WIP." + f"Command name {Bot.EXAM}")
        return ConversationHandler.END

    async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("There is nothing to cancel.")
    
    async def cancel_command_in_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Action canceled!")
        return ConversationHandler.END
    async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.message.reply_text("さようなら！")
        return ConversationHandler.END
    
    async def get_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text, kwargs = get_info.generate_bot_answer(update.message.text)

        await update.message.reply_text(text, **kwargs)
        return ConversationHandler.END
    
    async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("HELLO", callback_data=Bot.CallbackWorker.SETTINGS_HELLO)]]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("WIP", reply_markup=markup)

    UNKNOWN_COMMAND = MessageHandler(filters.COMMAND, unknown_command)

    CancelHandler = CommandHandler(CANCEL, cancel_command_in_conversation)
    
    COMMANDS = {
        START: CommandHandler(START, start_command),
        STOP: CommandHandler(STOP, stop_command),
        HELP: CommandHandler(HELP, help),
        CANCEL: CommandHandler(CANCEL, cancel_command),
        SETTINGS: CommandHandler(SETTINGS, settings_command)
    }

    ExamHandler = ConversationHandler(
            entry_points=[CommandHandler(EXAM, exam_command)],

            states={
                States.EXAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, exam_command)]
            },

            fallbacks=[COMMANDS[STOP]]
        )
    New_wordHandler = ConversationHandler(
        entry_points=[CommandHandler(NEW_WORDS, new_words_command)],
        states={
            States.NEW: []
        },
        fallbacks=[COMMANDS[STOP], COMMANDS[CANCEL]]
    )
    INFO_HANDLER = ConversationHandler(
        entry_points=[CommandHandler(GET_INFO, get_info_command)],
        states={
            States.GET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_info)]
        },
        fallbacks=[COMMANDS[STOP], COMMANDS[CANCEL]]
    )

    CallbackHandler = CallbackQueryHandler(CallbackWorker.on_click)
    # "UNKNOWN_COMMAND" MUST BE AT THE END OF THIS LIST
    HANDLERS = [
        ExamHandler,
        INFO_HANDLER,
        New_wordHandler,
        CallbackHandler,
        CancelHandler
        ] + list(COMMANDS.values()) + [UNKNOWN_COMMAND]


