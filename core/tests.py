import os
import subprocess
import sys
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase


class HeaderTests(TestCase):
    def test_guest_sees_login_links_even_on_profile(self):
        self.assertRedirects(self.client.get('/profile/'), '/login/?next=/profile/')

    def test_logged_in_user_sees_username(self):
        user = get_user_model().objects.create_user(username='student', password='test-password')
        self.client.force_login(user)
        response = self.client.get('/')
        self.assertContains(response, '>student</a>')
        self.assertContains(response, '>Выход</button>')
        self.assertNotContains(response, '>Войти</a>')


class EnvironmentTests(SimpleTestCase):
    def test_env_file_and_environment_priority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / 'application'
            app.mkdir()
            config = app / 'settings.py'
            config.write_text((settings.BASE_DIR / 'application/settings.py').read_text())
            (root / '.env.local').write_text('DJANGO_SECRET_KEY=test-file-key\nDJANGO_DEBUG=0\nDJANGO_ALLOWED_HOSTS=env.example\n')
            environment = os.environ.copy()
            for key in ['DJANGO_SECRET_KEY', 'DJANGO_DEBUG', 'DJANGO_ALLOWED_HOSTS', 'PYTHON_DOTENV_DISABLED', 'ENV_FILE']:
                environment.pop(key, None)
            script = (
                'import runpy, sys; s = runpy.run_path(sys.argv[1]); '
                'assert s["SECRET_KEY"] == sys.argv[2]; '
                'assert s["DEBUG"] is False; '
                'assert s["ALLOWED_HOSTS"] == ["env.example"]'
            )
            subprocess.run([sys.executable, '-c', script, str(config), 'test-file-key'], env=environment, check=True)
            environment['DJANGO_SECRET_KEY'] = 'test-process-key'
            subprocess.run([sys.executable, '-c', script, str(config), 'test-process-key'], env=environment, check=True)


class AccountTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('student', email='student@example.com', password='Useful-Password-847')

    def test_login_safe_next_and_invalid_password(self):
        data = {'username': 'student', 'password': 'Useful-Password-847', 'next': '/hot/?page=2'}
        self.assertRedirects(self.client.post('/login/', data), '/hot/?page=2')
        self.client.logout()
        data['next'] = 'https://evil.example/'
        self.assertRedirects(self.client.post('/login/', data), '/')
        self.client.logout()
        data['password'] = 'wrong'
        response = self.client.post('/login/', data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertContains(response, 'value="student"')

    def test_signup_validates_password_and_creates_profile(self):
        data = {'username': 'newuser', 'nickname': 'Антон', 'email': 'new@example.com', 'password1': '123', 'password2': '123'}
        response = self.client.post('/signup/', data)
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(get_user_model().objects.filter(username='newuser').exists())
        data.update(password1='Other-Password-847', password2='Other-Password-847')
        self.assertRedirects(self.client.post('/signup/', data), '/')
        self.assertEqual(get_user_model().objects.get(username='newuser').profile.user.username, 'newuser')

    def test_logout_is_post_and_preserves_local_page(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/logout/').status_code, 405)
        self.assertRedirects(self.client.post('/logout/', {'next': '/hot/'}), '/hot/')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertRedirects(self.client.post('/logout/', {'next': '//evil.example'}), '/')

    def test_profile_image_upload_and_validation(self):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        self.client.force_login(self.user)
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            data = {'email': 'updated@example.com', 'nickname': 'Новое имя'}
            data['avatar'] = SimpleUploadedFile('fake.png', b'not an image', content_type='image/png')
            response = self.client.post('/profile/', data)
            self.assertIn('avatar', response.context['form'].errors)
            stream = io.BytesIO()
            Image.new('RGB', (10, 10), 'red').save(stream, format='PNG')
            image = stream.getvalue()
            data['avatar'] = SimpleUploadedFile('big.png', image + b'x' * (5 * 1024 * 1024), content_type='image/png')
            self.assertIn('avatar', self.client.post('/profile/', data).context['form'].errors)
            data['avatar'] = SimpleUploadedFile('picture.png', image, content_type='image/png')
            self.assertRedirects(self.client.post('/profile/', data), '/profile/')
            self.user.refresh_from_db()
            self.assertEqual(self.user.email, 'updated@example.com')
            name = self.user.profile.avatar.name
            self.assertNotIn('picture', name)
            self.assertTrue((Path(directory) / name).exists())
            self.assertContains(self.client.get('/'), '/media/' + name)
