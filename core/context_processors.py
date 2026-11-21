def community(request):
    return {
        'popular_tags': ['python', 'django', 'javascript', 'html', 'css', 'bootstrap', 'git', 'linux', 'sql', 'docker', 'nginx', 'http', 'api', 'react', 'testing', 'postgresql', 'asyncio', 'web', 'career', 'algorithms'],
        'best_members': [{'name': name, 'rating': 2400 - i * 137} for i, name in enumerate(['Александр', 'Мария', 'Дмитрий', 'Екатерина', 'Антон', 'Иван', 'София', 'Михаил', 'Ольга', 'Никита'])],
    }
