from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST
from .forms import LoginForm, SignupForm, ProfileForm
from .models import Profile


def safe_next(request):
    target = request.POST.get('next', request.GET.get('next', ''))
    if url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return target
    return reverse('questions:index')


@require_http_methods(['GET', 'POST'])
def login(request):
    form = LoginForm(request, data=request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        auth_login(request, form.get_user())
        return redirect(safe_next(request))
    return render(request, 'core/login.html', {'form': form, 'next': safe_next(request), 'submit_label': 'Войти', 'form_kind': 'login'})


@require_http_methods(['GET', 'POST'])
def signup(request):
    form = SignupForm(request.POST if request.method == 'POST' else None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        auth_login(request, user)
        return redirect('questions:index')
    return render(request, 'core/signup.html', {'form': form, 'submit_label': 'Зарегистрироваться', 'form_kind': 'signup'})


@login_required
@require_http_methods(['GET', 'POST'])
def profile(request):
    instance, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST if request.method == 'POST' else None, request.FILES or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('core:profile')
    return render(request, 'core/profile.html', {'form': form, 'submit_label': 'Сохранить изменения'})


@require_POST
def logout(request):
    target = safe_next(request)
    auth_logout(request)
    return redirect(target)
