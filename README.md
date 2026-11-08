# AskSpace

Сервис вопросов и ответов на Django 5.2 и Bootstrap 5.3.

Запуск (Python 3.12+):

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Или через Docker:

```sh
docker compose up --build
```

Открыть http://127.0.0.1:8000/ .

Страницы: `/`, `/hot/`, `/tag/python/`, `/question/35/`, `/ask/`, `/login/`, `/signup/`, `/profile/`.

Данные-заглушки: обычно по 3 ответа; у вопроса №35 — 31 ответ для проверки пагинации. Формы данные не сохраняют.

Настройки читаются из `.env` в корне проекта. Переменные окружения имеют приоритет. В Git хранится только `.env.example`.
