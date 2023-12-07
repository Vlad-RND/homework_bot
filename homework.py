from http import HTTPStatus
import os
import time
import logging

from dotenv import load_dotenv
import requests
import telegram

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

# Не смог пока что разобраться с хендлерами
logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(funcName)s (%(lineno)d), %(message)s, %(name)s'
)


class CorrectResponceError(Exception):
    """Исключение, показывающее неправильность ответа от сервиса."""

    pass


class EmptyResponceError(Exception):
    """Пустой ответ от сервиса."""

    pass


def check_tokens():
    """Проверка наличия токенов и чат id."""
    tokens = (
        (PRACTICUM_TOKEN, 'Практикум токен'),
        (TELEGRAM_TOKEN, 'Телеграм токен'),
        (TELEGRAM_CHAT_ID, 'Чат ID')
    )
    check_result = True
    for token in tokens:
        if not token[0]:
            logging.critical(f'Отсутствует {token[1]}')
            check_result = False

    if not check_result:
        raise Exception('Отсутсвует токен или чат id')


def send_message(bot, message):
    """Отправка сообщения пользователю."""
    try:
        logging.debug(f'Попытка отправки сообщения {message}.')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'Сообщение {message} отправлено.')
        return True
    except telegram.error.TelegramError(message) as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')
        return False


def get_api_answer(timestamp):
    """Отправка запроса к эндпоинту и чтение json."""
    request_data = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp}
    }
    logging.debug(
        f'Запрос к {request_data["url"]}, параметры - {request_data["params"]}'
    )
    try:
        response = requests.get(
            request_data['url'],
            request_data['headers'],
            request_data['params']
        )
    except requests.RequestException:
        raise ConnectionError(
            f'URL - {request_data["url"]}'
            f'Headers - {request_data["headers"]}'
            f'Params - {request_data["params"]}'
        )

    if response.status_code != HTTPStatus.OK:
        raise CorrectResponceError(
            f'Status code - {response.status_code}'
            f'Reason - {response.reason}'
            f'Text - {response.text}'
        )
    return response.json()


def check_response(response):
    """Проверяем наличие ДЗ и достаем последнее."""
    logging.debug('Начало проверки ответа от сервиса.')
    if isinstance(response, dict):
        if 'homeworks' not in response:
            raise EmptyResponceError('Homework not in response')

        homeworks = response.get('homeworks')

        if isinstance(homeworks, list):
            return homeworks
        else:
            raise TypeError('Homeworks is not list')
    else:
        raise TypeError('Response is dict')


def parse_status(homework):
    """Приводим статус работы к понятному описанию."""
    try:
        homework_name = homework['homework_name']
        status = homework['status']
    except KeyError as error:
        logging.error(f'Отсутствует статус или имя домашней работы: {error}')

    if status not in HOMEWORK_VERDICTS.keys():
        logging.error(f'Неверный статус домашней работы: {status}')
        raise KeyError('Status not in HOMEWORK_VERDICTS')

    verdict = HOMEWORK_VERDICTS[status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0

    messages = {
        'current_report': '',
        'prev_report': ''
    }

    while True:
        try:
            response = get_api_answer(timestamp)
            homework_list = check_response(response)
            if homework_list:
                current_homework = homework_list[0]
                message = parse_status(current_homework)
            else:
                message = 'Нет новых статусов'

            if message != messages['current_report']:
                if send_message(bot, message):
                    messages['prev_report'] = messages['current_report']
                    messages['current_report'] = message
                    timestamp = response.get('current_date')
                else:
                    logging.debug(message)
        except EmptyResponceError as error:
            logging.error(f'Пустой ответ от API: {error}')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
