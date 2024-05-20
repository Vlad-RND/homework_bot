# homework_telegram_bot
### Описание проекта:

Telegram-bot для проверки статуса работы проекта на платформе "Яндекс Практикум".
Отправка запроса к API (ЯП), обработка ответа и отправка личного сообщения при обновлении данных.
Добавлена кнопка "/alive" для проверки работоспособности бота.

### Используемые библиотеки:

flake8==3.9.2,
flake8-docstrings==1.6.0,
pytest==6.2.5,
pytest-timeout==2.1.0,
python-dotenv==0.19.0,
python-telegram-bot==13.7,
requests==2.26.0

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Vlad-RND/homework_telegram_bot.git
```

```
cd homework_telegram_bot
```

Cоздать и активировать виртуальное окружение:

```
python -m venv env
```

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Создать и заполнить файл .env, пример заполнения:
```
PRACTICUM_TOKEN = ***
TELEGRAM_TOKEN = ***
TELEGRAM_CHAT_ID = ***
RETRY_PERIOD = ***
```

Запустить проект:

```
python homework.py
```

### Функционал бота:
- Делается запрос по токену;
- Расшифровывается ответ;
- Если ответ еще не был отправлен, отправляется сообщение указанному char_id в TG;
- Рекомендуемый RETRY_PERIOD = 600 секунд;
- Кнопка "/alive" для проверки активности бота.

Автор - Vlad-RND,
GIT - https://github.com/Vlad-RND