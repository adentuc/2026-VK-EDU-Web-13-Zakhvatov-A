from django import forms
from core.forms import StyledForm

class AskForm(StyledForm):
    title = forms.CharField(label='Заголовок', max_length=150, help_text='До 150 символов. Кратко сформулируйте суть вопроса.')
    text = forms.CharField(label='Текст вопроса', max_length=10000, widget=forms.Textarea(attrs={'rows': 7}), help_text='Опишите задачу и то, что уже попробовали. До 10 000 символов.')
    tags = forms.CharField(label='Теги', max_length=100, help_text='Не более трёх тегов через запятую, например: python, django.')

    def clean_tags(self):
        tags = [tag.strip() for tag in self.cleaned_data['tags'].split(',') if tag.strip()]
        if not 1 <= len(tags) <= 3:
            raise forms.ValidationError('Укажите от одного до трёх тегов.')
        return tags

class AnswerForm(StyledForm):
    text = forms.CharField(label='Ответ', max_length=10000, widget=forms.Textarea(attrs={'rows': 5}), help_text='До 10 000 символов.')
