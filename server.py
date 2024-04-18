from jishoreader import get_jisho_data
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import sqlite3
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class get_info:
    def generate_bot_answer(question: str) -> tuple[str, dict]:
        words = get_jisho_data(question, 1, 1)
        
        if words:
            word = words[0]
            if "exception" in word.keys():
                return ("Unexpected error caused. Try again later.", {})
            japanese = word["slug"]
            read = word["read"]
            out = f"{japanese}({read})\n\nDefinitions:"
            for index, pair in enumerate(word["definitions"]):
                translations = pair[0]
                parts_of_speech = pair[1]

                out += f"\n{','.join(parts_of_speech)}\n{index+1}. {','.join(translations)}\n"
            keyboard = [[InlineKeyboardButton("See also", url=f"https://jisho.org/word/{japanese}")]]
            markup = InlineKeyboardMarkup(keyboard)
            return (out, {"reply_markup": markup})
        else:
            return (f"""I Don't know the word {question}""", {})
    
    def write_to_DB(request: str):
        pass


def main():
    pass

if __name__ == "__main__":
    main()
    
