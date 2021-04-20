from flask import Flask, request
import logging
import json
# импортируем функции из нашего второго файла geo
from geo import get_country, get_distance, get_coordinates
import os

app = Flask(__name__)

# Добавляем логирование в файл.
# Чтобы найти файл, перейдите на pythonwhere в раздел files,
# он лежит в корневой папке
logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Request: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        # создаем словарь в который в будущем положим имя пользователя
        sessionStorage[user_id] = {
            'first_name': None,
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        # в последнем его сообщение ищем имя.
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
                          + '. Я - Алиса. Я могу показать город или сказать расстояние между городами!'
            return
    # Получаем города из нашего
    cities = get_cities(req)
    if not cities:
        res['response']['text'] = f'{sessionStorage[user_id]["first_name"]},ты не написал название не одного города!'
    elif len(cities) == 1:
        res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, этот город в стране - ' + \
                                  get_country(cities[0])
    elif len(cities) == 2:
        distance = get_distance(get_coordinates(
            cities[0]), get_coordinates(cities[1]))
        res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, расстояние между этими городами: ' + \
                                  str(round(distance)) + ' км.'
    else:
        res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, слишком много городов!'


def get_cities(req):
    cities = []
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            if 'city' in entity['value']:
                cities.append(entity['value']['city'])
    return cities


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
