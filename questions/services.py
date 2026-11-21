from django.db import transaction
from .models import Question, Answer, QuestionLike, AnswerLike


@transaction.atomic
def vote(user, target, value):
    # Блокировка объекта сериализует голоса и предотвращает потерю рейтинга.
    Model = type(target)
    target = Model.objects.select_for_update().get(pk=target.pk)
    Like, field = (QuestionLike, 'question') if isinstance(target, Question) else (AnswerLike, 'answer')
    lookup = {'user': user, field: target}
    previous = Like.objects.filter(**lookup).first()
    old_value = previous.value if previous else 0
    if value == old_value:
        value = 0
    if value == 0:
        if previous:
            previous.delete()
    elif previous:
        previous.value = value
        previous.save(update_fields=['value'])
    else:
        Like.objects.create(**lookup, value=value)
    target.rating += value - old_value
    target.save(update_fields=['rating'])
    return {'rating': target.rating, 'selected': value}
