import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import MessageHandler, filters, ConversationHandler, CommandHandler, ContextTypes, CallbackQueryHandler
from server import server
from jishoreader import OutKeys


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
        SELECTING_EXAM, EXAM, GET,EXAM_TEST, EXAM_TEST_EJ, EXAM_TEST_JE = range(6)

    class UserDataKeys():
        WORDS = "WORDS"
        
        EXAM_TYPE, EXAM_TESTED, EXAM_WORD, EXAM_COUNTS, EXAM_WRONGS = range(6, 11)

        NECESSARY_KEYS = [WORDS]

        DEFAULT_VALUES = {
            WORDS: []
        }
    
    class CallBackTypes:
        EXAM_ANSWER_1 = "EXAM_ANSWER_1"
        EXAM_ANSWER_2 = "EXAM_ANSWER_2"
        EXAM_ANSWER_3 = "EXAM_ANSWER_3"
        EXAM_ANSWER_4 = "EXAM_ANSWER_4"
        DONE = "DONE"

    async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"I don't know the command {update.message.text}")

    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        with open("help_text.txt") as f:
            text = f.read()
        await update.message.reply_text(text)

    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not len([k for k in context.user_data.keys() if k in Bot.UserDataKeys.NECESSARY_KEYS]) == len(Bot.UserDataKeys.NECESSARY_KEYS):
            for key in Bot.UserDataKeys.NECESSARY_KEYS:
                context.user_data[key] = Bot.UserDataKeys.DEFAULT_VALUES[key]

            await update.message.reply_text(f"こんにちは、お客さん！")
            await Bot.help(update, context)
        else:
            await update.message.reply_text(f"Hmm... It seems like you have already started.")

    async def new_words_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if Bot.UserDataKeys.WORDS not in context.user_data.keys():
            await update.message.reply_text("You did not /start")
            return ConversationHandler.END
        try:
            word, number = server.get_new_word(context.user_data[Bot.UserDataKeys.WORDS])
        except Exception as e:
            await update.message.reply_text(e.args[0])
            return ConversationHandler.END
        japanese = word[OutKeys.SLUG]
        read = word[OutKeys.READ]
        out = f"{japanese}({read})\n\nDefinitions:"
        for index, pair in enumerate(word[OutKeys.DEFINITIONS]):
            translations = pair[OutKeys.ENGLISH]
            parts_of_speech = pair[OutKeys.PARTS_OF_SPEECH]

            out += f"\n{', '.join(parts_of_speech)}\n{index+1}. {'; '.join(translations)}\n"
        keyboard = [[InlineKeyboardButton("See also", url=f"https://jisho.org/word/{japanese}")]]
        markup = InlineKeyboardMarkup(keyboard)
        context.user_data[Bot.UserDataKeys.WORDS].append(number)
        await update.message.reply_text(out, reply_markup=markup)

    async def get_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Please specify the word you are interested in.")
        return Bot.States.GET

    async def exam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if Bot.UserDataKeys.WORDS not in context.user_data.keys():
            await update.message.reply_text("You did not /start")
            return ConversationHandler.END
        if not context.user_data[Bot.UserDataKeys.WORDS] or len(context.user_data[Bot.UserDataKeys.WORDS]) < 4:
            await update.message.reply_text("Sorry, You can't take an exam because I don't know words you have learned.")
            return ConversationHandler.END
        keyboard = [
            [InlineKeyboardButton("English to Japanese test", callback_data=str(Bot.States.EXAM_TEST_EJ))],
            [InlineKeyboardButton("Japanese to English test", callback_data=str(Bot.States.EXAM_TEST_JE))],
            ]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("What type of exam would you like to start?", reply_markup=markup)
        return Bot.States.SELECTING_EXAM
        
    async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("There is nothing to cancel.")
        return ConversationHandler.END
    
    async def cancel_command_in_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Action canceled!")
        return ConversationHandler.END
    
    async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.message.reply_text("さようなら！")
        return ConversationHandler.END
    
    async def get_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text, kwargs = server.generate_bot_answer(update.message.text)

        await update.message.reply_text(text, **kwargs)
        return ConversationHandler.END

    def exam_end_get_text(context: ContextTypes.DEFAULT_TYPE):
        rig = context.user_data[Bot.UserDataKeys.EXAM_COUNTS][0]
        count = context.user_data[Bot.UserDataKeys.EXAM_COUNTS][1]
        text = f"Thank you for this exam!\nRight answers: {rig}\nAnswers Count: {count}"
        while context.user_data[Bot.UserDataKeys.EXAM_WRONGS]:
            l_id = context.user_data[Bot.UserDataKeys.EXAM_WRONGS].pop()
            word = server.find_word_by_learning(l_id)
            tx = f'\nWrong word - {word[OutKeys.SLUG]}\n\t{"; ".join(word[OutKeys.DEFINITIONS][0][OutKeys.ENGLISH])}\n'
            text += tx
        return text
    
    def exam_init(etype, context: ContextTypes.DEFAULT_TYPE):
        context.user_data[Bot.UserDataKeys.EXAM_TYPE] = etype
        context.user_data[Bot.UserDataKeys.EXAM_TESTED] = []
        context.user_data[Bot.UserDataKeys.EXAM_COUNTS] = [0, 0]
        context.user_data[Bot.UserDataKeys.EXAM_WRONGS] = []
        
    def exam_check_answer(answer, context: ContextTypes.DEFAULT_TYPE):

        context.user_data[Bot.UserDataKeys.EXAM_COUNTS][1] += 1
        if context.user_data[Bot.UserDataKeys.EXAM_WORD] == answer:
            context.user_data[Bot.UserDataKeys.EXAM_COUNTS][0] += 1
        else:
            context.user_data[Bot.UserDataKeys.EXAM_WRONGS] += [context.user_data[Bot.UserDataKeys.EXAM_TESTED][-1]]
            
    async def test_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_answer = update.callback_query.data
        if  user_answer == str(Bot.States.EXAM_TEST_EJ) or user_answer == str(Bot.States.EXAM_TEST_JE):
            Bot.exam_init(user_answer, context)
        elif user_answer == Bot.CallBackTypes.DONE:
            text = Bot.exam_end_get_text(context)
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text)
            return ConversationHandler.END
        elif user_answer[:-1] == "EXAM_ANSWER_":
            ans = int(user_answer[-1]) - 1
            Bot.exam_check_answer(ans, context)


        exam_type = context.user_data[Bot.UserDataKeys.EXAM_TYPE]
        try:
            if exam_type == str(Bot.States.EXAM_TEST_EJ):
                question, a1, a2, a3, a4, right, l_id = server.create_exam_ej_question(context.user_data[Bot.UserDataKeys.WORDS], context.user_data[Bot.UserDataKeys.EXAM_TESTED])
            elif exam_type == str(Bot.States.EXAM_TEST_JE):
                question, a1, a2, a3, a4, right, l_id = server.create_exam_je_question(context.user_data[Bot.UserDataKeys.WORDS], context.user_data[Bot.UserDataKeys.EXAM_TESTED])
        except Exception as e:
            if e.args[0] == "Not enough words":
                text = Bot.exam_end_get_text(context)
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(text)
                return ConversationHandler.END
            else:
                logging.error(e)
                await update.callback_query.answer()
                await update.callback_query.edit_message_text("Unexpected error caused. Try later")
                return ConversationHandler.END
        context.user_data[Bot.UserDataKeys.EXAM_TESTED].append(l_id)


        markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(a1, callback_data=Bot.CallBackTypes.EXAM_ANSWER_1),
            InlineKeyboardButton(a2, callback_data=Bot.CallBackTypes.EXAM_ANSWER_2)],
        [
            InlineKeyboardButton(a3, callback_data=Bot.CallBackTypes.EXAM_ANSWER_3),
            InlineKeyboardButton(a4, callback_data=Bot.CallBackTypes.EXAM_ANSWER_4)
        ],
            [InlineKeyboardButton("quit", callback_data=Bot.CallBackTypes.DONE)]])
        context.user_data[Bot.UserDataKeys.EXAM_WORD] = right
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(question, reply_markup=markup)
        return Bot.States.EXAM_TEST


    UNKNOWN_COMMAND = MessageHandler(filters.COMMAND, unknown_command)

    CancelHandler = CommandHandler(CANCEL, cancel_command_in_conversation)
    
    COMMANDS = {
        START: CommandHandler(START, start_command),
        STOP: CommandHandler(STOP, stop_command),
        HELP: CommandHandler(HELP, help),
        CANCEL: CommandHandler(CANCEL, cancel_command),
        NEW_WORDS: CommandHandler(NEW_WORDS, new_words_command)
    }
    Exam_SELECT_Callback = [
        CallbackQueryHandler(test_exam,pattern="^" + str(States.EXAM_TEST_EJ) + "$"),
        CallbackQueryHandler(test_exam,pattern="^" + str(States.EXAM_TEST_JE) + "$")
    ]
    ExamHandler = ConversationHandler(
            entry_points=[CommandHandler(EXAM, exam_command)],

            states={
                States.SELECTING_EXAM: Exam_SELECT_Callback,
                States.EXAM_TEST: [CallbackQueryHandler(test_exam)],
            },

            fallbacks=[COMMANDS[STOP], CancelHandler]
        )
    
    INFO_HANDLER = ConversationHandler(
        entry_points=[CommandHandler(GET_INFO, get_info_command)],
        states={
            States.GET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_info)]
        },
        fallbacks=[COMMANDS[STOP], CancelHandler]
    )

    # "UNKNOWN_COMMAND" MUST BE AT THE END OF THIS LIST
    HANDLERS = [
        ExamHandler,
        INFO_HANDLER
        ] + list(COMMANDS.values()) + [UNKNOWN_COMMAND]