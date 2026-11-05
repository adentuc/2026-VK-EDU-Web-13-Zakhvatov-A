from django import forms

class StyledForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class LoginForm(StyledForm):
    login = forms.CharField(label='Логин', max_length=80)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput, max_length=128)

class SignupForm(StyledForm):
    email = forms.EmailField(label='Электронная почта', max_length=254, help_text='Например, name@example.com')
    nickname = forms.CharField(label='Никнейм', max_length=80)
    password = forms.CharField(label='Пароль', min_length=8, max_length=128, widget=forms.PasswordInput, help_text='Не менее 8 символов.')
    password_repeat = forms.CharField(label='Повторите пароль', max_length=128, widget=forms.PasswordInput)
    avatar = forms.FileField(label='Аватар', required=False, help_text='Выберите изображение для аватара.')

    def clean(self):
        data = super().clean()
        if data.get('password') != data.get('password_repeat'):
            self.add_error('password_repeat', 'Пароли не совпадают.')
        return data

class ProfileForm(StyledForm):
    email = forms.EmailField(label='Электронная почта', max_length=254)
    nickname = forms.CharField(label='Никнейм', max_length=80)
    avatar = forms.FileField(label='Новый аватар', required=False, help_text='Выберите изображение для аватара.')
