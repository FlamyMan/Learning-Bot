from jishoreader import get_jisho_data
import json


class get_info:
    def generate_bot_answer(question: str) -> str:
        words = get_jisho_data(question, 1, 1)
        if words:
            word = words[0]
            japanese = word["slug"]
            read = word["read"]
            out = f"{japanese}({read})\n\nDefinitions:"
            for index, pair in enumerate(word["definitions"]):
                translations = pair[0]
                parts_of_speech = pair[1]

                out += f"\n{','.join(parts_of_speech)}\n{index+1}. {','.join(translations)}\n"
            out += f"\n\nSee also https://jisho.org/word/{japanese}"
            return out
        else:
            return f"""I Don't know the word {question}"""
    
