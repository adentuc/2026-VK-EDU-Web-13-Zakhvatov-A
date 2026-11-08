from django.test import SimpleTestCase, RequestFactory, override_settings
from django.urls import reverse
from .data import QUESTIONS
from .pagination import paginate


class PaginationTests(SimpleTestCase):
    def test_invalid_page_falls_back_to_first(self):
        for value in ['', 'abc', '0', '-1', '99999999999999999', '1.5']:
            with self.subTest(value=value):
                page = paginate(list(range(45)), RequestFactory().get('/', {'page': value}), 20)
                self.assertEqual(page.number, 1)
                self.assertEqual(len(page), 20)

    def test_second_and_empty_pages(self):
        page = paginate(list(range(45)), RequestFactory().get('/?page=3'), 20)
        self.assertEqual(list(page), list(range(40, 45)))
        self.assertEqual(paginate([], RequestFactory().get('/')).number, 1)


class PageTests(SimpleTestCase):
    def test_all_required_routes(self):
        for path in ['/', '/hot/', '/tag/python/', '/question/35/', '/login/', '/signup/', '/profile/', '/ask/']:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Популярные теги')
                self.assertContains(response, '/static/css/bootstrap.min.css')
                self.assertNotContains(response, 'https://cdn')

    def test_ordering_and_filtering(self):
        new = self.client.get('/').context['page_obj']
        hot = self.client.get('/hot/').context['page_obj']
        tagged = self.client.get('/tag/python/').context['page_obj']
        self.assertEqual(new[0]['id'], 1)
        self.assertEqual(hot[0]['rating'], max(q['rating'] for q in QUESTIONS))
        self.assertTrue(all('python' in q['tags'] for q in tagged))
        self.assertEqual(len(new), 20)
        self.assertEqual(len(self.client.get('/question/35/').context['page_obj']), 30)
        self.assertEqual(len(self.client.get('/question/6/').context['page_obj']), 3)
        self.assertEqual(len(self.client.get('/question/35/?page=2').context['page_obj']), 1)

    def test_search_persists_in_pagination_links(self):
        response = self.client.get('/', {'q': 'Как', 'page': 2})
        self.assertEqual(response.context['page_obj'].number, 2)
        self.assertContains(response, 'q=%D0%9A%D0%B0%D0%BA&amp;page=1')
        self.assertTrue(all('как' in (q['title'] + ' ' + q['text']).casefold() for q in response.context['page_obj']))

    def test_empty_results_and_unknown_question(self):
        self.assertContains(self.client.get('/tag/unknown/'), 'Вопросов пока нет')
        self.assertContains(self.client.get('/', {'q': 'no-matching-string'}), 'Вопросов пока нет')
        self.assertEqual(self.client.get('/question/99999/').status_code, 404)
        with override_settings(DEBUG=False):
            self.assertContains(self.client.get('/missing/'), 'Страница не найдена', status_code=404)

    def test_forms_show_field_and_form_errors(self):
        self.assertContains(self.client.post('/signup/', {'email': 'bad'}), 'Введите правильный адрес')
        self.assertContains(self.client.post('/ask/', {'title': 'Тест', 'text': 'Текст', 'tags': 'a,b,c,d'}), 'Укажите от одного до трёх тегов')
        self.assertContains(self.client.post('/login/', {'login': 'user', 'password': 'password'}), 'Сохранение данных пока недоступно')
        self.assertContains(self.client.post('/question/35/', {'text': 'Ответ'}), 'не сохранён')

    def test_method_and_csrf_protection(self):
        from django.test import Client
        self.assertEqual(self.client.post('/').status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post('/ask/', {}).status_code, 403)
