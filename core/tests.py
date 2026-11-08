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
        response = self.client.get('/profile/')
        self.assertContains(response, '>Войти</a>')
        self.assertNotContains(response, '>Выход</a>')

    def test_logged_in_user_sees_username(self):
        user = get_user_model().objects.create_user(username='student', password='test-password')
        self.client.force_login(user)
        response = self.client.get('/')
        self.assertContains(response, '>student</a>')
        self.assertContains(response, '>Выход</a>')
        self.assertNotContains(response, '>Войти</a>')


class EnvironmentTests(SimpleTestCase):
    def test_env_file_and_environment_priority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / 'application'
            app.mkdir()
            config = app / 'settings.py'
            config.write_text((settings.BASE_DIR / 'application/settings.py').read_text())
            (root / '.env').write_text('DJANGO_SECRET_KEY=test-file-key\nDJANGO_DEBUG=0\nDJANGO_ALLOWED_HOSTS=env.example\n')
            environment = os.environ.copy()
            for key in ['DJANGO_SECRET_KEY', 'DJANGO_DEBUG', 'DJANGO_ALLOWED_HOSTS', 'PYTHON_DOTENV_DISABLED']:
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
