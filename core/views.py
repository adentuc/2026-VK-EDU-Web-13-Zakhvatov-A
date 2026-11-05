from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .forms import LoginForm, SignupForm, ProfileForm


def form_page(request, template, form_class, label, **context):
    form = form_class(request.POST if request.method == 'POST' else None, request.FILES or None, initial=context.pop('initial', None))
    if request.method == 'POST' and form.is_valid():
        form.add_error(None, 'Сохранение данных пока недоступно.')
    return render(request, template, {'form': form, 'submit_label': label, **context})

@require_http_methods(['GET', 'POST'])
def login(request):
    return form_page(request, 'login.html', LoginForm, 'Войти', form_kind='login')

@require_http_methods(['GET', 'POST'])
def signup(request):
    return form_page(request, 'signup.html', SignupForm, 'Зарегистрироваться', form_kind='signup')

@require_http_methods(['GET', 'POST'])
def profile(request):
    return form_page(request, 'profile.html', ProfileForm, 'Сохранить изменения', show_user_menu=True, initial={'email': 'anton@example.com', 'nickname': 'Антон'})
