from uuid import uuid4
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count, Sum
from faker import Faker
from core.models import Profile
from questions.models import Question, Answer, Tag, QuestionLike, AnswerLike


def batches(total, build, model, size=2000):
    for start in range(0, total, size):
        model.objects.bulk_create([build(i) for i in range(start, min(start + size, total))], batch_size=size)


class Command(BaseCommand):
    help = 'Добавить данные: ratio пользователей, 10*ratio вопросов, 100*ratio ответов, ratio тегов, 200*ratio оценок.'

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int)

    @transaction.atomic
    def handle(self, *args, **options):
        ratio = options['ratio']
        if ratio < 2:
            raise CommandError('ratio должен быть не меньше 2: при ratio=1 недостаточно уникальных пар для 200 оценок.')
        fake = Faker('ru_RU')
        prefix = uuid4().hex[:12]
        User = get_user_model()
        batches(ratio, lambda i: User(username=f'{prefix}_{i}', email=f'{prefix}_{i}@example.com', password='!'), User)
        users = list(User.objects.filter(username__startswith=prefix).order_by('pk').values_list('pk', flat=True))
        batches(ratio, lambda i: Profile(user_id=users[i]), Profile)
        batches(ratio, lambda i: Tag(name=f'{prefix}-{i}'), Tag)
        tags = list(Tag.objects.filter(name__startswith=prefix).order_by('pk').values_list('pk', flat=True))
        batches(ratio * 10, lambda i: Question(title=f'{prefix}: {fake.sentence(nb_words=6)}'[:150], text=fake.paragraph(), author_id=users[i % ratio]), Question)
        questions = list(Question.objects.filter(author_id__in=users).order_by('pk').values_list('pk', flat=True))
        Through = Question.tags.through
        batches(len(questions), lambda i: Through(question_id=questions[i], tag_id=tags[i % ratio]), Through)
        batches(ratio * 100, lambda i: Answer(question_id=questions[i % len(questions)], author_id=users[i % ratio], text=fake.paragraph()), Answer)
        answers = list(Answer.objects.filter(question_id__in=questions).order_by('pk').values_list('pk', flat=True))
        question_votes = min(ratio * 100, ratio * len(questions))
        answer_votes = ratio * 200 - question_votes
        batches(question_votes, lambda i: QuestionLike(user_id=users[(i // len(questions)) % ratio], question_id=questions[i % len(questions)], value=1), QuestionLike)
        batches(answer_votes, lambda i: AnswerLike(user_id=users[(i // len(answers)) % ratio], answer_id=answers[i % len(answers)], value=1), AnswerLike)
        for start in range(0, len(questions), 2000):
            items = list(Question.objects.filter(pk__in=questions[start:start+2000]).annotate(total=Sum('likes__value')))
            for item in items:
                item.rating = item.total or 0
            Question.objects.bulk_update(items, ['rating'], batch_size=2000)
        for start in range(0, len(answers), 2000):
            items = list(Answer.objects.filter(pk__in=answers[start:start+2000]).annotate(total=Sum('likes__value')))
            for item in items:
                item.rating = item.total or 0
            Answer.objects.bulk_update(items, ['rating'], batch_size=2000)
        self.stdout.write(self.style.SUCCESS(f'Добавлено: {ratio} пользователей, {ratio*10} вопросов, {ratio*100} ответов, {ratio} тегов, {ratio*200} оценок.'))
