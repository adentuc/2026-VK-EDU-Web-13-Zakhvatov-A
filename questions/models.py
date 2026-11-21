from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Count, Q
from django.urls import reverse


class QuestionQuerySet(models.QuerySet):
    def listing(self):
        return self.select_related('author__profile').prefetch_related('tags').annotate(answer_count=Count('answers'))

    def new(self):
        return self.order_by('-created', '-pk')

    def best(self):
        return self.order_by('-rating', '-created', '-pk')

    def by_tag(self, tag):
        return self.filter(tags__name=tag).best()

    def search(self, term):
        return self.filter(Q(title__icontains=term) | Q(text__icontains=term)) if term else self


validate_tag_name = RegexValidator(
    r'^[^\W_][\w.+#-]*\Z',
    'Начните тег с буквы или цифры. Используйте буквы, цифры и знаки _ . + # -.',
)


class Tag(models.Model):
    name = models.CharField('название', max_length=32, unique=True, validators=[validate_tag_name])

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return self.name


class Question(models.Model):
    title = models.CharField('заголовок', max_length=150)
    text = models.TextField('текст', max_length=10000)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='questions', verbose_name='автор')
    tags = models.ManyToManyField(Tag, related_name='questions', verbose_name='теги')
    created = models.DateTimeField('дата создания', auto_now_add=True, db_index=True)
    rating = models.IntegerField('рейтинг', default=0, db_index=True)
    objects = QuestionQuerySet.as_manager()

    class Meta:
        verbose_name = 'вопрос'
        verbose_name_plural = 'вопросы'
        indexes = [models.Index(fields=['-rating', '-created'])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('questions:question', args=[self.pk])


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name='вопрос')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='answers', verbose_name='автор')
    text = models.TextField('текст', max_length=10000)
    created = models.DateTimeField('дата создания', auto_now_add=True)
    rating = models.IntegerField('рейтинг', default=0)
    correct = models.BooleanField('правильный ответ', default=False)

    class Meta:
        ordering = ['-rating', 'created', 'pk']
        verbose_name = 'ответ'
        verbose_name_plural = 'ответы'
        constraints = [models.UniqueConstraint(fields=['question'], condition=Q(correct=True), name='one_correct_answer')]
        indexes = [models.Index(fields=['question', '-rating', 'created'])]

    def __str__(self):
        return self.text[:60]


class QuestionLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='пользователь')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='likes', verbose_name='вопрос')
    value = models.SmallIntegerField('оценка', choices=[(-1, 'Не нравится'), (1, 'Нравится')])

    class Meta:
        verbose_name = 'оценка вопроса'
        verbose_name_plural = 'оценки вопросов'
        constraints = [models.UniqueConstraint(fields=['user', 'question'], name='unique_question_vote'), models.CheckConstraint(condition=Q(value__in=[-1, 1]), name='question_vote_value')]

    def __str__(self):
        return f'{self.user_id}: {self.value}'


class AnswerLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='пользователь')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='likes', verbose_name='ответ')
    value = models.SmallIntegerField('оценка', choices=[(-1, 'Не нравится'), (1, 'Нравится')])

    class Meta:
        verbose_name = 'оценка ответа'
        verbose_name_plural = 'оценки ответов'
        constraints = [models.UniqueConstraint(fields=['user', 'answer'], name='unique_answer_vote'), models.CheckConstraint(condition=Q(value__in=[-1, 1]), name='answer_vote_value')]

    def __str__(self):
        return f'{self.user_id}: {self.value}'
