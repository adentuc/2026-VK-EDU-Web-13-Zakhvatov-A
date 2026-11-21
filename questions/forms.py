from django import forms
from django.db import transaction
from core.forms import StyledFormMixin
from .models import Question, Answer, Tag, validate_tag_name


class AskForm(StyledFormMixin, forms.ModelForm):
    tags = forms.CharField(label='Теги', max_length=100, help_text='От одного до трёх тегов через запятую.')

    class Meta:
        model = Question
        fields = ['title', 'text', 'tags']
        widgets = {'text': forms.Textarea(attrs={'rows': 7})}

    def clean_tags(self):
        tags = list(dict.fromkeys(tag.strip().lower() for tag in self.cleaned_data['tags'].split(',') if tag.strip()))
        if not 1 <= len(tags) <= 3 or any(len(tag) > 32 for tag in tags):
            raise forms.ValidationError('Укажите от одного до трёх тегов длиной до 32 символов.')
        for tag in tags:
            validate_tag_name(tag)
        return tags

    @transaction.atomic
    def save(self, author):
        question = super().save(commit=False)
        question.author = author
        question.save()
        question.tags.set([Tag.objects.get_or_create(name=name)[0] for name in self.cleaned_data['tags']])
        return question


class AnswerForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text']
        widgets = {'text': forms.Textarea(attrs={'rows': 5})}

    def save(self, author, question):
        answer = super().save(commit=False)
        answer.author = author
        answer.question = question
        answer.save()
        return answer


class VoteForm(forms.Form):
    value = forms.TypedChoiceField(choices=[(-1, 'Не нравится'), (0, 'Отменить'), (1, 'Нравится')], coerce=int)


class CorrectAnswerForm(forms.Form):
    question = forms.ModelChoiceField(queryset=Question.objects.all())
    answer = forms.ModelChoiceField(queryset=Answer.objects.all())
    correct = forms.TypedChoiceField(choices=[('1', 'Выбрать'), ('0', 'Снять')], coerce=lambda value: value == '1')

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        question, answer = data.get('question'), data.get('answer')
        if question and question.author_id != self.user.pk:
            raise forms.ValidationError('Только автор вопроса может выбрать правильный ответ.', code='forbidden')
        if question and answer and answer.question_id != question.pk:
            raise forms.ValidationError('Ответ относится к другому вопросу.')
        return data

    @transaction.atomic
    def save(self):
        question = Question.objects.select_for_update().get(pk=self.cleaned_data['question'].pk)
        answer = question.answers.select_for_update().get(pk=self.cleaned_data['answer'].pk)
        if self.cleaned_data['correct']:
            question.answers.filter(correct=True).exclude(pk=answer.pk).update(correct=False)
            question.answers.filter(pk=answer.pk).update(correct=True)
            return answer.pk
        question.answers.filter(pk=answer.pk).update(correct=False)
        return question.answers.filter(correct=True).values_list('pk', flat=True).first()
