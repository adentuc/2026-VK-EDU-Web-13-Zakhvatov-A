from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from core.models import Profile
from .models import Question, Answer, Tag, QuestionLike, AnswerLike


class DatabasePagesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('student')
        Profile.objects.create(user=self.user)

    def test_empty_pages_and_404(self):
        self.assertContains(self.client.get('/'), 'Вопросов пока нет')
        self.assertEqual(self.client.get('/question/9999/').status_code, 404)
        self.assertEqual(self.client.get('/tag/missing/').status_code, 404)
        question = Question.objects.create(title='Вопрос', text='Текст', author=self.user)
        self.assertContains(self.client.get(question.get_absolute_url()), 'Пока нет ни одного ответа')

    def test_unique_votes(self):
        question = Question.objects.create(title='Вопрос', text='Текст', author=self.user)
        QuestionLike.objects.create(user=self.user, question=question, value=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            QuestionLike.objects.create(user=self.user, question=question, value=-1)

    def test_fill_counts_and_rating(self):
        call_command('fill_db', 2, verbosity=0)
        self.assertEqual(Question.objects.count(), 20)
        self.assertEqual(Answer.objects.count(), 200)
        self.assertEqual(Tag.objects.count(), 2)
        self.assertEqual(QuestionLike.objects.count()+AnswerLike.objects.count(), 400)
        question = Question.objects.listing().best().first()
        self.assertEqual(question.rating, question.likes.count())

    def test_queries_do_not_grow_with_page_size(self):
        Question.objects.bulk_create([Question(title=f'Вопрос {i}', text='Текст', author=self.user) for i in range(25)])
        with self.assertNumQueries(2):
            for question in Question.objects.listing()[:20]:
                list(question.tags.all())
                str(question.author.profile)


class WriteTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('author')
        Profile.objects.create(user=self.user)
        self.other = get_user_model().objects.create_user('other')
        self.question = Question.objects.create(author=self.user, title='Первый вопрос', text='Текст')
        self.answer = Answer.objects.create(author=self.other, question=self.question, text='Первый ответ')

    def test_guest_cannot_write_or_vote(self):
        self.assertEqual(self.client.get('/ask/').status_code, 302)
        self.assertEqual(self.client.post(self.question.get_absolute_url(), {'text': 'Ответ'}).status_code, 302)
        self.assertEqual(self.client.post(f'/api/question/{self.question.pk}/vote/', {'value': 1}).status_code, 401)
        self.assertContains(self.client.get('/'), 'Войдите, чтобы голосовать')

    def test_ask_validation_and_tags(self):
        self.client.force_login(self.user)
        response = self.client.post('/ask/', {'title': 'Вопрос', 'text': 'Текст', 'tags': 'a,b,c,d'})
        self.assertIn('tags', response.context['form'].errors)
        self.assertEqual(Question.objects.count(), 1)
        response = self.client.post('/ask/', {'title': 'Вопрос', 'text': 'Текст', 'tags': 'web/http'})
        self.assertIn('tags', response.context['form'].errors)
        response = self.client.post('/ask/', {'title': 'Вопрос', 'text': 'Текст', 'tags': 'python, django, python'})
        question = Question.objects.order_by('-pk').first()
        self.assertRedirects(response, question.get_absolute_url())
        self.assertEqual(set(question.tags.values_list('name', flat=True)), {'python', 'django'})

    def test_answer_redirects_to_second_page_and_anchor(self):
        Answer.objects.bulk_create([Answer(author=self.other, question=self.question, text=f'Ответ {i}') for i in range(29)])
        self.client.force_login(self.user)
        response = self.client.post(self.question.get_absolute_url(), {'text': 'Новый ответ'})
        answer = Answer.objects.order_by('-pk').first()
        self.assertEqual(response['Location'], self.question.get_absolute_url()+f'?page=2#answer-{answer.pk}')
        self.assertContains(self.client.get(self.question.get_absolute_url()+'?page=2'), 'Новый ответ')

    def test_vote_change_cancel_and_validation(self):
        self.client.force_login(self.user)
        for kind, target, Model in [('question', self.question, QuestionLike), ('answer', self.answer, AnswerLike)]:
            url = f'/api/{kind}/{target.pk}/vote/'
            self.assertEqual(self.client.post(url, {'value': 1}).json()['rating'], 1)
            page = self.client.get(self.question.get_absolute_url())
            self.assertContains(page, 'aria-pressed="true"')
            self.assertEqual(self.client.post(url, {'value': -1}).json()['rating'], -1)
            self.assertEqual(self.client.post(url, {'value': -1}).json()['rating'], 0)
            self.assertEqual(Model.objects.count(), 0)
            self.assertEqual(self.client.post(url, {'value': 9}).status_code, 400)
            self.assertEqual(self.client.get(url).status_code, 405)
            target.refresh_from_db()
            self.assertEqual(target.rating, 0)
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(f'/api/question/{self.question.pk}/vote/', {'value': 1})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['code'], 'csrf')

    def test_correct_answer_requires_author_and_matching_question(self):
        data = {'question': self.question.pk, 'answer': self.answer.pk, 'correct': '1'}
        self.client.force_login(self.other)
        self.assertEqual(self.client.post('/api/correct/', data).status_code, 403)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post('/api/correct/', data).json()['answer_id'], self.answer.pk)
        second = Answer.objects.create(author=self.other, question=self.question, text='Другой ответ')
        data['answer'] = second.pk
        self.client.post('/api/correct/', data)
        self.assertEqual(self.question.answers.filter(correct=True).count(), 1)
        self.assertTrue(self.question.answers.get(pk=second.pk).correct)
        unrelated = Question.objects.create(author=self.user, title='Другой', text='Текст')
        data['question'] = unrelated.pk
        self.assertEqual(self.client.post('/api/correct/', data).status_code, 400)
        data.update(question=self.question.pk, correct='0')
        self.assertIsNone(self.client.post('/api/correct/', data).json()['answer_id'])


class AdminTests(TestCase):
    def test_all_model_admin_pages(self):
        admin = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'Admin-Password-847')
        Profile.objects.create(user=admin)
        question = Question.objects.create(author=admin, title='Вопрос', text='Текст')
        Answer.objects.create(author=admin, question=question, text='Ответ')
        self.client.force_login(admin)
        for path in ['/admin/', '/admin/core/profile/', '/admin/questions/question/', '/admin/questions/answer/', '/admin/questions/tag/', '/admin/questions/questionlike/', '/admin/questions/answerlike/', f'/admin/auth/user/{admin.pk}/change/', f'/admin/questions/question/{question.pk}/change/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
