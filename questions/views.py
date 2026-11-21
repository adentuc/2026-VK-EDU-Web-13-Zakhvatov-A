from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.csrf import csrf_failure as default_csrf_failure
from django.views.decorators.http import require_GET, require_http_methods
from .models import Question, Answer, Tag
from .forms import AskForm, AnswerForm, VoteForm, CorrectAnswerForm
from .services import vote
from .pagination import paginate


def listing(request, template, heading, objects, active_tab):
    search = request.GET.get('q', '').strip()[:200]
    return render(request, template, {'heading': heading, 'page_obj': paginate(objects.search(search).with_votes(request.user), request, 20), 'active_tab': active_tab, 'search': search})


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


@require_http_methods(['GET', 'POST'])
def question(request, question_id):
    item = get_object_or_404(Question.objects.listing().with_votes(request.user), pk=question_id)
    if request.method == 'POST' and not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), reverse('core:login'))
    form = AnswerForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        return redirect(form.save(request.user, item).get_absolute_url())
    page = paginate(item.answers.with_votes(request.user), request, 30)
    return render(request, 'question.html', {'question': item, 'page_obj': page, 'form': form, 'submit_label': 'Опубликовать ответ'})


@login_required
@require_http_methods(['GET', 'POST'])
def ask(request):
    form = AskForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        return redirect(form.save(request.user).get_absolute_url())
    return render(request, 'ask.html', {'form': form, 'submit_label': 'Опубликовать вопрос'})


def ajax_error(message, status_code, code):
    return JsonResponse({'status': 'error', 'code': code, 'message': message}, status=status_code)


def ajax_post(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.method != 'POST':
            response = ajax_error('Требуется POST.', 405, 'method_not_allowed')
            response['Allow'] = 'POST'
            return response
        if not request.user.is_authenticated:
            return ajax_error('Войдите в аккаунт.', 401, 'no_auth')
        return view(request, *args, **kwargs)
    return wrapped


def csrf_failure(request, reason=''):
    route = request.resolver_match
    if route and route.view_name in {
        'questions:question_vote', 'questions:answer_vote', 'questions:correct_answer',
    }:
        return ajax_error('Обновите страницу и попробуйте ещё раз.', 403, 'csrf')
    return default_csrf_failure(request, reason=reason)


def vote_response(request, model, target_id):
    form = VoteForm(request.POST)
    if not form.is_valid():
        return ajax_error(form.errors.as_text(), 400, 'bad_params')
    target = model.objects.filter(pk=target_id).first()
    if target is None:
        return ajax_error('Объект не найден.', 404, 'not_found')
    try:
        result = vote(request.user, target, form.cleaned_data['value'])
    except model.DoesNotExist:
        return ajax_error('Объект не найден.', 404, 'not_found')
    return JsonResponse({'status': 'ok', **result})


@ajax_post
def question_vote(request, question_id):
    return vote_response(request, Question, question_id)


@ajax_post
def answer_vote(request, answer_id):
    return vote_response(request, Answer, answer_id)


@ajax_post
def correct_answer(request):
    form = CorrectAnswerForm(request.POST, user=request.user)
    if not form.is_valid():
        if form.has_error('__all__', 'forbidden'):
            return ajax_error('Только автор вопроса может выбрать правильный ответ.', 403, 'forbidden')
        return ajax_error(form.errors.as_text(), 400, 'bad_params')
    try:
        answer_id = form.save()
    except (Question.DoesNotExist, Answer.DoesNotExist):
        return ajax_error('Вопрос или ответ не найден.', 404, 'not_found')
    return JsonResponse({'status': 'ok', 'answer_id': answer_id})
