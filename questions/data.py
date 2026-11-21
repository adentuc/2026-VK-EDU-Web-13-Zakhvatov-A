"""Данные-заглушки для страниц вопросов и ответов."""
from datetime import datetime, timedelta, timezone

TOPICS = [
    ('Как правильно организовать структуру Django-проекта?', 'Разбираюсь с разделением проекта на приложения. Где хранить общие шаблоны и статические файлы, чтобы код оставался понятным?', ['python', 'django']),
    ('В чём разница между flexbox и CSS Grid?', 'Хочу сделать адаптивную сетку карточек. В каких случаях удобнее использовать flexbox, а когда лучше выбрать grid?', ['css', 'html']),
    ('Как отменить последний коммит, сохранив изменения?', 'Случайно добавил незаконченные изменения в коммит. Как вернуть файлы в рабочую директорию и ничего не потерять?', ['git', 'web']),
    ('Почему fetch не отправляет cookie на сервер?', 'Запрос проходит успешно, но сервер не видит сессию пользователя. Какие настройки запроса и CORS нужно проверить?', ['javascript', 'http']),
    ('Как работает пагинация в Django?', 'Нужно разбить список вопросов на страницы и обработать несуществующий номер страницы. Как использовать Paginator?', ['python', 'django']),
    ('Как подключить Bootstrap без CDN?', 'Хочу хранить все зависимости локально, чтобы интерфейс работал без внешних сервисов. Как подключить CSS и JavaScript?', ['bootstrap', 'html']),
]
BASE_TIME = datetime(2026, 11, 5, 9, 0, tzinfo=timezone.utc)
QUESTIONS = []
for i in range(1, 36):
    title, text, tags = TOPICS[(i - 1) % len(TOPICS)]
    QUESTIONS.append({
        'id': i,
        'title': title if i <= 6 else f'{title} ({i})',
        'text': text,
        'tags': tags,
        'author': ['Антон', 'Мария', 'Дмитрий'][(i - 1) % 3],
        'created': BASE_TIME - timedelta(hours=i),
        'rating': (i * 7) % 25,
        'selected': [0, 1, -1][i % 3],
        'answer_count': 31 if i == 35 else 3,
    })


def answers_for(question_id):
    texts = [
        'Попробуйте сначала сделать простой пример и проверить его отдельно.',
        'У меня была похожая проблема. Помог пример из документации.',
        'Спасибо, первый способ помог разобраться.',
    ]
    answers = []
    count = 31 if question_id == 35 else 3
    for i in range(1, count + 1):
        answers.append({
            'id': i,
            'text': texts[(i - 1) % len(texts)],
            'author': ['Мария', 'Антон', 'Иван'][(i - 1) % 3],
            'created': BASE_TIME - timedelta(minutes=i),
            'rating': count - i,
            'selected': 0,
            'correct': i == 1,
        })
    return answers
