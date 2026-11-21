from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods
from core.views import form_page
from .data import QUESTIONS, answers_for
from .forms import AskForm, AnswerForm
from .pagination import paginate


def listing(request, template, heading, objects, active_tab):
    search = request.GET.get('q', '').strip()[:200]
    if search:
        objects = [q for q in objects if search.casefold() in (q['title'] + ' ' + q['text']).casefold()]
    return render(request, template, {'heading': heading, 'page_obj': paginate(objects, request, 20), 'active_tab': active_tab, 'search': search})

@require_GET
def index(request):
    return listing(request, 'index.html', 'Новые вопросы', sorted(QUESTIONS, key=lambda q: q['created'], reverse=True), 'new')

@require_GET
def hot(request):
    return listing(request, 'hot.html', 'Популярные вопросы', sorted(QUESTIONS, key=lambda q: q['rating'], reverse=True), 'hot')

@require_GET
def tag(request, tag):
    objects = sorted([q for q in QUESTIONS if tag in q['tags']], key=lambda q: q['rating'], reverse=True)
    return listing(request, 'tag.html', f'Вопросы по тегу {tag}', objects, '')

@require_http_methods(['GET', 'POST'])
def question(request, question_id):
    item = next((q for q in QUESTIONS if q['id'] == question_id), None)
    if item is None:
        raise Http404('Вопрос не найден')
    form = AnswerForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        form.add_error(None, 'Ответ не сохранён. Сохранение данных пока недоступно.')
    return render(request, 'question.html', {'question': item, 'page_obj': paginate(sorted(answers_for(question_id), key=lambda a: (-a['rating'], a['created'])), request, 30), 'form': form, 'submit_label': 'Опубликовать ответ'})

@require_http_methods(['GET', 'POST'])
def ask(request):
    return form_page(request, 'ask.html', AskForm, 'Опубликовать вопрос')
