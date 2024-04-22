from jishoreader import get_jisho_data, OutKeys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import sqlite3
import logging
import math
import ast
import random


DATABASE_PATH = "ServerDataBase.db"
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class server:
    CONNECTION = sqlite3.connect(DATABASE_PATH)

    def generate_bot_answer(question: str) -> tuple[str, dict]:
        words = get_jisho_data(question, 1, 1)
        
        if words:
            word = words[0]
            if OutKeys.EXCEPTION in word.keys():
                return ("Unexpected error caused. Try again later.", {})
            japanese = word[OutKeys.SLUG]
            read = word[OutKeys.READ]
            out = f"{japanese}({read})\n\nDefinitions:"
            for index, pair in enumerate(word[OutKeys.DEFINITIONS]):
                translations = pair[OutKeys.ENGLISH]
                parts_of_speech = pair[OutKeys.PARTS_OF_SPEECH]

                out += f"\n{', '.join(parts_of_speech)}\n{index+1}. {'; '.join(translations)}\n"
            keyboard = [[InlineKeyboardButton("See also", url=f"https://jisho.org/word/{japanese}")]]
            markup = InlineKeyboardMarkup(keyboard)
            return (out, {"reply_markup": markup})
        else:
            return (f"""I Don't know the word {question}""", {})
        
    def formated_jisho_data(request, lim=math.inf) -> list[dict]:
        data = get_jisho_data(request, limit=lim)
        if not data or (OutKeys.EXCEPTION in set([tuple(t.keys()) for t in data])):
            logging.warning("The data is empty or exception")
            return
        
        for word in data:
            definitions = word[OutKeys.DEFINITIONS]
            for defition in definitions:
                en = defition[OutKeys.ENGLISH]
                pos = defition[OutKeys.PARTS_OF_SPEECH]
                for i in range(len(en)):
                    en[i] = en[i].replace("'", "\\")
                    en[i] = en[i].replace('"', "||")
                for i in range(len(pos)):
                    pos[i] = pos[i].replace("'", "\\")
                    pos[i] = pos[i].replace('"', "||")
        return data
    
    def write_word_to_DB(word: dict) -> None:
        # word => definition => pos
        cursor = server.CONNECTION.cursor()
        
        japanese = word[OutKeys.SLUG]
        read = word[OutKeys.READ]
        definitions = word[OutKeys.DEFINITIONS]
        logging.info(f"SELECT id FROM Words WHERE word == \"{japanese}\" and read == \"{read}\"")
        found = cursor.execute(f"SELECT id FROM Words WHERE word == \"{japanese}\" and read == \"{read}\"").fetchall()
        if not found:
            logging.info(f"INSERT INTO Words(word, read) VALUES({japanese},{read})")
            cursor.execute(f"""INSERT INTO Words(word, read)
                        VALUES ("{japanese}", "{read}")""").fetchall()
            word_id, *_ = cursor.execute(f"SELECT id FROM Words WHERE word == \"{japanese}\" and read == \"{read}\"").fetchone()
            for d in definitions:
                en = d[OutKeys.ENGLISH]
                pos = d[OutKeys.PARTS_OF_SPEECH]
                cursor.execute(f"""INSERT INTO definitions(word_id, definition)
                        VALUES ({word_id}, "{en}")""")
                d_id, *_ = cursor.execute(f"SELECT id FROM definitions WHERE word_id == {word_id} and definition == \"{en}\"").fetchone()                
                cursor.execute(f"""
                        INSERT INTO parts_of_speech(word_id, definition_id, parts_of_speech)
                        VALUES ({word_id}, {d_id}, \"{pos}\")""")
        server.CONNECTION.commit()
    
    def add_learn_material(request, lim=math.inf) -> None:
        data = server.formated_jisho_data(request, lim)
        cursor = server.CONNECTION.cursor()
        
        for word in data:
            japanese = word[OutKeys.SLUG]
            read = word[OutKeys.READ]
            found = cursor.execute(f"SELECT id FROM Words WHERE word == \"{japanese}\" and read == \"{read}\"").fetchall()
            while not found:
                server.write_word_to_DB(word)
                found = cursor.execute(f"SELECT id FROM Words WHERE word == \"{japanese}\" and read == \"{read}\"").fetchall()
            l_found = cursor.execute(f"SELECT id FROM learning Where word_id = {found[0][0]}").fetchall()
            if not l_found:
                logging.info(f"INSERT INTO learning(word_id) VALUES(\"{found[0][0]}\")")
                cursor.execute(f"INSERT INTO learning(word_id) VALUES(\"{found[0][0]}\")")
        server.CONNECTION.commit()
    
    def find_word_in_DB(word_id)-> dict:
        cursor = server.CONNECTION.cursor()
        word_raw = cursor.execute(f"""
                            SELECT
                                Words.word,
                                Words.read,
                                parts_of_speech.parts_of_speech,
                                definitions.definition
                            FROM Words
                            INNER JOIN parts_of_speech
                                ON parts_of_speech.word_id = Words.id
                            INNER JOIN definitions
                                ON definitions.id = parts_of_speech.definition_id
                            WHERE 
                                Words.id = {word_id}
        """).fetchall()
        slugs = set()
        reads = set()
        definitions = list()
        for i in range(len(word_raw)):
            slug, read, pos, en = word_raw[i]
            slugs.add(slug)
            reads.add(read)
            definitions.append({OutKeys.ENGLISH: ast.literal_eval(en), OutKeys.PARTS_OF_SPEECH: ast.literal_eval(pos)})
        if len(slugs) != 1:
            raise Exception("the word has more than one writing or no one")
        if len(reads) != 1:
            raise Exception("the word has more than one reading or no one")
        return {
            OutKeys.SLUG: slug,
            OutKeys.READ: read,
            OutKeys.DEFINITIONS: definitions
        }
    
    def find_word_id_by_learning(learning_id) -> int:
        cursor = server.CONNECTION.cursor()
        word_id, = cursor.execute(f"""SELECT word_id FROM learning WHERE id == {learning_id}""").fetchone()
        return word_id
    
    def find_word_by_learning(learning_id) -> dict:
        word_id = server.find_word_id_by_learning(learning_id)
        return server.find_word_in_DB(word_id)


    def get_new_word(previous_words: list[int]):
        cursor = server.CONNECTION.cursor()
        ids_raw = cursor.execute("""SELECT id FROM learning""").fetchall()
        ids = set([i[0] for i in ids_raw])
        user = set(previous_words)
        vals = ids - user
        if not vals:
            raise Exception("No new words available")
        n = min(vals)
        word_id, = cursor.execute(f"""SELECT word_id FROM learning WHERE id == {n}""").fetchone()
        return (server.find_word_in_DB(word_id), n)
    
    def create_exam_ej_question(learned_words: list[int], tested_words: list[int]):
        words = list(set(learned_words) - set(tested_words))
        if len(words) < 4:
            raise Exception("Not enough words")
        rndn = random.choice(words)
        word = server.find_word_by_learning(rndn)
        question = "; ".join(word[OutKeys.DEFINITIONS][0][OutKeys.ENGLISH])
        right = word[OutKeys.SLUG]
        answers = {right}
        while len(answers) < 4:
            r = random.choice(learned_words)
            w = server.find_word_by_learning(r)[OutKeys.SLUG]
            answers.add(w)
        answers = list(answers)
        random.shuffle(answers)
        right_n = 0
        for i, ans in enumerate(answers):
            if ans == right:
                right_n = i
                break
        return (question, *answers, right_n, rndn)
    
    def create_exam_je_question(learned_words: list[int], tested_words: list[int]):
        words = list(set(learned_words) - set(tested_words))
        if len(words) < 4:
            raise Exception("Not enough words")
        rndn = random.choice(words)
        word = server.find_word_by_learning(rndn)
        question = word[OutKeys.SLUG]
        right = "; ".join(word[OutKeys.DEFINITIONS][0][OutKeys.ENGLISH])
        answers = {right}
        while len(answers) < 4:
            r = random.choice(learned_words)
            w = "; ".join(server.find_word_by_learning(r)[OutKeys.DEFINITIONS][0][OutKeys.ENGLISH])
            answers.add(w)
        answers = list(answers)
        random.shuffle(answers)
        right_n = 0
        for i, ans in enumerate(answers):
            if ans == right:
                right_n = i
                break
        return (question, *answers, right_n, rndn)



    
