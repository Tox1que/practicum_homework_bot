import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    filemode='w'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('hmwrk.log', maxBytes=5 * 10**6, backupCount=5)
formatter = logging.Formatter('%(asctime)s, %(levelname)s,'
                              '%(message)s, %(name)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework_name is None:
        return f'Название: {homework_name}'
    homework_status = homework.get('status')
    status_verdict = {
        'rejected': 'К сожалению, в работе нашлись ошибки.',
        'approved': 'Ревьюеру всё понравилось, работа зачтена!',
    }
    if homework_status not in status_verdict.keys():
        return f'Статус: {homework_status}'
    return (f'У вас проверили работу "{homework_name}"!\n'
            f'\n{status_verdict.get(homework_status)}')


def get_homeworks(current_timestamp):
    url = URL
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    payload = {'from_date': current_timestamp
               if current_timestamp is not None else int(time.time())}
    try:
        homework_statuses = requests.get(url=url, headers=headers,
                                         params=payload)
    except requests.exceptions.RequestException as e:
        logger.error(e, exc_info=True)
        raise requests.exceptions.RequestException(repr(e))
    try:
        return homework_statuses.json()
    except ValueError as e:
        logger.error(e, exc_info=True)
        raise ValueError(repr(e))
    except TypeError as e:
        logger.error(e, exc_info=True)
        raise TypeError(repr(e))


def send_message(message):
    return bot.send_message(CHAT_ID, message)


def main():
    timestamps = {'current': int(time.time())}
    while True:
        try:
            if get_homeworks(timestamps['current'])['homeworks']:
                homework = get_homeworks(timestamps['current'])['homeworks'][0]
                message = parse_homework_status(homework)
                logger.info(send_message(message))
                timestamps.update(
                    current=get_homeworks(
                        timestamps['current']).get('current_date'))
                time.sleep(5 * 60)
        except Exception as e:
            print(f'Бот упал с ошибкой: {e}')
            logger.error(e, exc_info=True)
            send_message(f'Бот упал с ошибкой: {e}')
            time.sleep(60)


if __name__ == '__main__':
    main()
