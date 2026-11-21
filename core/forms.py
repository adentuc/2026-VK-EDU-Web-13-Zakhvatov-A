from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.validators import FileExtensionValidator
from django.db import transaction
from .models import Profile


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if self.is_bound and name in self.errors:
                field.widget.attrs['class'] += ' is-invalid'
                field.widget.attrs['aria-invalid'] = 'true'


class StyledForm(StyledFormMixin, forms.Form):
    pass


def avatar_field():
    return forms.ImageField(label='Аватар', required=False, validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])], help_text='JPG, PNG или WebP. Не более 5 МБ.')


class AvatarMixin:
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and avatar.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Размер изображения не должен превышать 5 МБ.')
        return avatar


class LoginForm(StyledFormMixin, AuthenticationForm):
    pass


class SignupForm(AvatarMixin, StyledFormMixin, UserCreationForm):
    email = forms.EmailField(label='Электронная почта')
    nickname = forms.CharField(label='Имя', max_length=150)
    avatar = avatar_field()

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ['username', 'email', 'nickname', 'password1', 'password2', 'avatar']

    def clean_email(self):
        email = self.cleaned_data['email']
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Этот email уже используется.')
        return email

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['nickname']
        if commit:
            user.save()
            Profile.objects.create(user=user, avatar=self.cleaned_data.get('avatar') or '')
        return user


class ProfileForm(AvatarMixin, StyledFormMixin, forms.ModelForm):
    email = forms.EmailField(label='Электронная почта')
    nickname = forms.CharField(label='Имя', max_length=150)
    avatar = avatar_field()

    class Meta:
        model = Profile
        fields = ['email', 'nickname', 'avatar']

    def __init__(self, *args, **kwargs):
        profile = kwargs.get('instance')
        kwargs.setdefault('initial', {}).update(email=profile.user.email, nickname=profile.user.first_name)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']
        if get_user_model().objects.exclude(pk=self.instance.user_id).filter(email__iexact=email).exists():
            raise forms.ValidationError('Этот email уже используется.')
        return email

    @transaction.atomic
    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.user.email = self.cleaned_data['email']
            profile.user.first_name = self.cleaned_data['nickname']
            profile.user.save(update_fields=['email', 'first_name'])
            profile.save()
        return profile
