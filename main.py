from flask import Flask, request
import logging
import json
import random
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# создаем словарь, в котором ключ — название города,
# а значение — массив, где перечислены id картинок,
# которые мы записали в прошлом пункте.

cities = {
    'москва': (['1030494/e03dd6cbae8a79d9d43b',
               '1652229/83a36487ffdc7aa60ea6'], 'россия'),
    'нью-йорк': (['1652229/aa05a7a54bd5101fe0f6',
                 '1521359/103a9d92c4564eef8a64'], 'сша'),
    'париж': (["1030494/6e5717e4148f18216d12",
              '213044/4016b2ee880fa2a0895b'], 'франция')
}

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
        res['response']['text'] = 'Привет! Назови свое имя!'
        # создаем словарь в который в будущем положим имя пользователя
        sessionStorage[user_id] = {
            'first_name': None,
            'start_game': False,
            'now_city': None,
            'guessed_city': [],
            'images_for_show': [],
            'user_right_answer_city': False
        }
        return

    if 'payload' in req['request'] and 'help' in req['request']['payload']:
        res['response']['text'] = 'Это справка'
        return

    # если пользователь не новый, то попадаем сюда.
    # если поле имени пустое, то это говорит о том,
    # что пользователь еще не представился.
    if sessionStorage[user_id]['first_name'] is None:
        # в последнем его сообщение ищем имя.
        if req['request']['original_utterance'].lower() != 'помощь':
            first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
            return
        # если нашли, то приветствуем пользователя.
        # И спрашиваем какой город он хочет увидеть.
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться, ' \
                          + first_name.title() \
                          + '. Я - Алиса. Сыграем в угадай город?'
            # получаем варианты buttons из ключей нашего словаря cities
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]
            return
    if req['request']['original_utterance'].lower() == 'нет' and not(sessionStorage[user_id]['start_game']):
        res['response']['text'] = 'Тогда, пока'
        res['response']['end_session'] = True
        return
    # если мы знакомы с пользователем и он нам что-то написал,
    # то это говорит о том, что он уже говорит о городе,
    # что хочет увидеть.
    if req['request']['original_utterance'].lower() == 'да' and not(sessionStorage[user_id]['start_game']):
        sessionStorage[user_id]['start_game'] = True
        stay_cities = []
        for elem in cities.keys():
            if elem not in sessionStorage[user_id]['guessed_city']:
                stay_cities.append(elem)
        city = random.choice(stay_cities)
        sessionStorage[user_id]['guessed_city'].append(city)
        sessionStorage[user_id]['now_city'] = city
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за город?'
        image_for_show = random.choice(cities[city][0])
        sessionStorage[user_id]['images_for_show'].append(image_for_show)
        res['response']['card']['image_id'] = image_for_show
        res['response']['text'] = 'Что это за город?'
        return
    if not(sessionStorage[user_id]['start_game']):
        res['response']['text'] = 'Не поняла. Так да или нет?'
        res['response']['buttons'] = [
            {
                'title': 'Да',
                'hide': True
            },
            {
                'title': 'Нет',
                'hide': True
            }
        ]
        return
    else:
        if sessionStorage[user_id]['user_right_answer_city']:
            answer_user = get_country(req)
        else:
            answer_user = get_city(req)
        if answer_user == sessionStorage[user_id]['now_city']:
            sessionStorage[user_id]['user_right_answer_city'] = True
            res['response']['text'] = 'Правильно! А в какой стране находится этот город?'
            return
        if sessionStorage[user_id]['user_right_answer_city'] and answer_user is None:
            res['response']['text'] = 'Похоже, такой страны нет.'
            return
        if sessionStorage[user_id]['user_right_answer_city'] and \
                answer_user.lower() != cities[sessionStorage[user_id]['now_city']][1]:
            res['response']['text'] = 'Неправильно'
            return
        if answer_user is None or answer_user != sessionStorage[user_id]['now_city']:
            if sessionStorage[user_id]['images_for_show'] == cities[sessionStorage[user_id]['now_city']]:
                res['response']['text'] = f'Вы пытались. Это {sessionStorage[user_id]["now_city"]}.' \
                                          f'Сыграем еще?'
                sessionStorage[user_id]['now_city'] = None
                sessionStorage[user_id]['start_game'] = False
                sessionStorage[user_id]['guessed_city'] = []
                sessionStorage[user_id]['images_for_show'] = []
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    }
                ]
                return
            images_city = []
            for elem in cities[sessionStorage[user_id]['now_city']][0]:
                if elem not in sessionStorage[user_id]['images_for_show']:
                    images_city.append(elem)
            image_for_show = random.choice(images_city)
            sessionStorage[user_id]['images_for_show'].append(image_for_show)
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = 'Вот еще фотография этого города. Есть мысли?'
            res['response']['card']['image_id'] = image_for_show
            res['response']['text'] = 'Вот еще фотография этого города. Есть мысли?'
            return
        elif sessionStorage[user_id]['user_right_answer_city'] and \
                answer_user.lower() == cities[sessionStorage[user_id]['now_city']][1]:

            if len(sessionStorage[user_id]['guessed_city']) == len(list(cities.keys())):
                res['response']['text'] = 'Что ж, у меня закончились все города. Приходи позже, поиграем.'
                res['response']['end_session'] = True
                return
            res['response']['text'] = 'Правильно. Сыграем еще?'
            sessionStorage[user_id]['start_game'] = False
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    'title': 'Покажи город на карте',
                    'url': f'https://yandex.ru/maps/?mode=search&text={sessionStorage[user_id]["now_city"]}',
                    'hide': True
                }
            ]


def get_city(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO то пытаемся получить город(city),
        # если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('city', None)


def get_country(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO то пытаемся получить город(city),
        # если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('country', None)


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
