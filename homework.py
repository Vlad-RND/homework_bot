from http import HTTPStatus
import os
import sys
import time
import requests


from dotenv import load_dotenv
import telegram
import logging

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)


def check_tokens():
    """Проверка наличия токенов и чат id."""
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.critical('Отсутствует токен или chat ID')
        sys.exit()


def send_message(bot, message):
    """Отправка сообщения пользователю."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'Сообщение {message} отправлено.')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(timestamp):
    """Отправка запроса к эндпоинту и чтение json."""
    check_tokens()
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except Exception as error:
        logging.error(f'Ошибка при отправке запроса: {error}')

    if response.status_code != HTTPStatus.OK:
        logging.error(
            f'Эндпоинт недоступен, status code: {response.status_code}'
        )
        raise Exception
    return response.json()


def check_response(response):
    """Проверяем наличие ДЗ и достаем последнее."""
    if not isinstance(response, dict):
        raise TypeError
    elif 'homeworks' not in response:
        raise KeyError
    elif not isinstance(response['homeworks'], list):
        raise TypeError
    elif response['homeworks'][0]:
        return response['homeworks'][0]

    logging.debug('Отсутствие в ответе новых статусов.')


def parse_status(homework):
    """Приводим статус работы к понятному описанию."""
    try:
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[homework['status']]
    except KeyError as error:
        logging.error(f'Неожиданный статус домашней работы: {error}')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        message = ''
        try:
            response = get_api_answer(timestamp)
            current_homework = check_response(response)
            message = parse_status(current_homework)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'

        if message != '':
            send_message(bot, message)

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
