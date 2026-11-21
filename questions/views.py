from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_http_methods
from core.views import form_page
from .models import Question, Tag
from .forms import AskForm, AnswerForm
from .pagination import paginate


def listing(request, template, heading, objects, active_tab):
    search = request.GET.get('q', '').strip()[:200]
    return render(request, template, {'heading': heading, 'page_obj': paginate(objects.search(search), request, 20), 'active_tab': active_tab, 'search': search})


@require_GET
def index(request):
    return listing(request, 'index.html', 'Новые вопросы', Question.objects.listing().new(), 'new')


@require_GET
def hot(request):
    return listing(request, 'hot.html', 'Популярные вопросы', Question.objects.listing().best(), 'hot')


@require_GET
def tag(request, tag):
    tag = get_object_or_404(Tag, name=tag)
    return listing(request, 'tag.html', f'Вопросы по тегу {tag}', Question.objects.listing().by_tag(tag.name), '')


@require_GET
def question(request, question_id):
    item = get_object_or_404(Question.objects.listing(), pk=question_id)
    page = paginate(item.answers.select_related('author__profile'), request, 30)
    return render(request, 'question.html', {'question': item, 'page_obj': page, 'form': AnswerForm(), 'submit_label': 'Опубликовать ответ'})


@require_http_methods(['GET', 'POST'])
def ask(request):
    return form_page(request, 'ask.html', AskForm, 'Опубликовать вопрос')
