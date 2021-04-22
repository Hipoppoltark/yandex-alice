from flask import Flask, request
import logging
import json
import requests
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# создаем словарь, где для каждого пользователя
# мы будем хранить его имя
sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False,
            "buttons": [
                {
                    "title": "Помощь",
                    "payload": {
                        "help": True
                    },
                    "hide": True
                }
            ]
        },
    }
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    # если пользователь новый, то просим его представиться.
    if req['session']['new']:
        res['response']['text'] = 'Привет! Я алиса, могу перевести любое слово на английский!'
        # создаем словарь в который в будущем положим имя пользователя
        sessionStorage[user_id] = {
            'first_name': None,
            'start_game': False,
            'now_city': None,
            'guessed_city': [],
            'images_for_show': []
        }
        return

    if 'payload' in req['request'] and 'help' in req['request']['payload']:
        res['response']['text'] = 'Это справка'
        return

    if 'переведите слово ' in req['request']['original_utterance'].lower() or \
        'переведи слово ' in req['request']['original_utterance'].lower():
        word_for_translate = req['request']['original_utterance'].lower().split('слово ')[1]

        url = "https://translated-mymemory---translation-memory.p.rapidapi.com/api/get"

        querystring = {"q": word_for_translate, "langpair": "ru|en", "de": "a@b.c", "onlyprivate": "0", "mt": "1"}

        headers = {
            'x-rapidapi-key': "99c2b5a669msha54ad475f0264d5p16cd1bjsn0c3d45cf22e2",
            'x-rapidapi-host': "translated-mymemory---translation-memory.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers, params=querystring).json()

        res['response']['text'] = response['responseData']['translatedText']
        return
    else:
        res['response']['text'] = 'Я не понимаю, что вы от меня хотите'


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

