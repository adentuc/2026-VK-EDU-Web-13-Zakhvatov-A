# AskSpace — ДЗ3

Python 3.12+, PostgreSQL 15+. Из корня проекта:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env.local
# Указать параметры своей PostgreSQL в .env.local
python manage.py migrate
python manage.py fill_db 20
python manage.py createsuperuser
python manage.py runserver
```

Docker: скопировать `.env.example` в `.env.docker`, задать пароль БД и ключ Django, выполнить `docker compose up --build`.

Страницы: `/`, `/hot/`, `/tag/<название>/`, `/question/<id>/`, `/ask/`, `/login/`, `/signup/`, `/profile/`, `/admin/`.

`fill_db ratio` (ratio ≥ 2) добавляет ratio пользователей и тегов, ratio*10 вопросов, ratio*100 ответов, ratio*200 оценок. Для объёмов строго больше минимумов из задания нужен ratio=10001. Данные создаются пакетами, команда добавляет новый набор и не удаляет старые записи.

Проверка: `python manage.py test`. Debug toolbar включена только при DEBUG=1. В ДЗ3 формы остаются макетами; запись через сайт добавляется в ДЗ4.
