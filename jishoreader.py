import math
import requests
import subprocess
import argparse
import time
import logging
import json


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)
class OutKeys():
    SLUG = "slug"
    READ = "read"
    DEFINITIONS = "definitions"
    ENGLISH = "en"
    PARTS_OF_SPEECH = "parts_of_speech"
    EXCEPTION = "exception"

def parse_word(word) -> dict:
    try:
        slug = word["slug"]
        read = word["japanese"][0]["reading"]
        definitions = [
            {
                OutKeys.ENGLISH: sens["english_definitions"],
                OutKeys.PARTS_OF_SPEECH: sens["parts_of_speech"]
            } for sens in word["senses"]]
        return {
            OutKeys.SLUG: slug,
            OutKeys.READ: read,
            OutKeys.DEFINITIONS: definitions
                }
    except Exception:
        logging.exception(f"Cannot get word{word}")
        return ""

def parse_json(json):
    return [parse_word(word) for word in json]

def get_jisho_data(question: str, page: int=1, limit: int=math.inf) -> list:
    if page <= 0:
        raise ValueError("Argument \"page\" must be a Natural number")
    if limit < page:
        raise ValueError("Argument \"limit\" must be greater than \"page\"")
    raw = "https://jisho.org/api/v1/search/words?keyword={quest}&page={page}"
    question = question.replace('#', '%23')
    question = question.replace(' ', '%20')

    out = []
    
    while True:
        done = raw.format(quest=question, page=page)
        logging.info(done)
        try:
            get: dict = requests.get(done).json()
            if "data" in get.keys():
                data = get["data"]
            else:
                break
        except Exception as e:
            logging.exception(e)
            return [{OutKeys.EXCEPTION: 1}]
        if not data:
            break
        out += parse_json(data)
        if page >= limit:
            break
        page += 1
        time.sleep(5)
    logging.info(f"ended page {page}")
    return out
    

def write_jisho_to_file(question: str, page=1, limit=math.inf, output='out.json', show_exp=False):
    data = get_jisho_data(question, page=page, limit=limit)
    stringdata = json.dumps(data, ensure_ascii=False)
    with open(output, "w", encoding="UTF-8") as f:
        f.write(stringdata)
        if show_exp:
            subprocess.Popen(rf'explorer /select,{f.name}')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('search_for', type=str, help='Your question to https://jisho.org/')
    parser.add_argument('--start', default=1, type=int, help='First page(min 1)')
    parser.add_argument('--limit', default=math.inf, type=int, help='Limit page')
    parser.add_argument('--output', default='out.json', type=str, help='Output file')
    parser.add_argument('--showExplorer', default=False, type=bool, help='Show File in Explorer after end')
    parser.add_argument('--DebugMode', default=False, type=bool, help='debug')
    args = parser.parse_args()
    _question: str = args.search_for
    _page = args.start
    _limit = args.limit
    _output = args.output
    _showExp = args.showExplorer
    
    write_jisho_to_file(_question, _page, _limit, _output, _showExp)

if __name__ == '__main__':
    main()
    

