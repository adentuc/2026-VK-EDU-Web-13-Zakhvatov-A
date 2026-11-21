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
