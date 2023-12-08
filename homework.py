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


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

hendler_for_file = logging.FileHandler(f'{__file__} + .log', mode='w')
console_hendler = logging.StreamHandler()

formatter = logging.Formatter(
    '''%(asctime)s, %(levelname)s, %(funcName)s (%(lineno)d),
    %(message)s, %(name)s'''
)

hendler_for_file.setFormatter(formatter)
console_hendler.setFormatter(formatter)

logger.addHandler(hendler_for_file)
logger.addHandler(console_hendler)


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
    for token, name in tokens:
        if not token:
            logging.critical(f'Отсутствует {name}')
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
        'Запрос к {url}, параметры - {params}'.format(
            **request_data
        )
    )
    try:
        response = requests.get(**request_data)
    except requests.RequestException:
        raise ConnectionError(
            'URL - {url}. Headers - {headers}. Params - {params}.'.format(
                **request_data
            )
        )

    if response.status_code != HTTPStatus.OK:
        raise CorrectResponceError(
            'Status code {status_code}. Reason {reason}. Text {text}.'.format(
                **response
            )
        )
    return response.json()


def check_response(response):
    """Проверяем наличие ДЗ и достаем последнее."""
    logging.debug('Начало проверки ответа от сервиса.')
    if not isinstance(response, dict):
        raise TypeError('Response is dict')
    if 'homeworks' not in response:
        raise EmptyResponceError('Homework not in response')

    homeworks = response.get('homeworks')

    if not isinstance(homeworks, list):
        raise TypeError('Homeworks is not list')

    return homeworks


def parse_status(homework):
    """Приводим статус работы к понятному описанию."""
    try:
        homework_name = homework['homework_name']
        status = homework['status']
    except KeyError as error:
        logging.error(f'Отсутствует статус или имя домашней работы: {error}')

    if status not in HOMEWORK_VERDICTS:
        raise ValueError('Status not in HOMEWORK_VERDICTS')

    verdict = HOMEWORK_VERDICTS[status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0

    current_report = ''
    prev_report = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homework_list = check_response(response)
            if homework_list:
                current_homework = homework_list[0]
                current_report = parse_status(current_homework)
            else:
                current_report = 'Нет новых статусов'

            if current_report != prev_report:
                if send_message(bot, current_report):
                    prev_report = current_report
                    timestamp = response.get('current_date', 0)
                else:
                    logging.debug(current_report)
        except EmptyResponceError as error:
            logging.error(f'Пустой ответ от API: {error}')
        except Exception as error:
            current_report = f'Сбой в работе программы: {error}'
            logging.exception(current_report)
            if current_report != prev_report:
                send_message(bot, current_report)
                prev_report = current_report
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
