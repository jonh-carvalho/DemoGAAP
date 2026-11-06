import json
import os
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, LiveServerTestCase, SimpleTestCase, TestCase, override_settings

from gaap.models import Perfil
from gaap.page_views import _api_call


class RailwaySettingsTests(SimpleTestCase):
    def run_settings(self, **variables):
        env = os.environ.copy()
        for name in ('SECRET_KEY', 'ALLOWED_HOSTS', 'CSRF_TRUSTED_ORIGINS'):
            env.pop(name, None)
        env.update(variables)
        return subprocess.run(
            [
                sys.executable,
                '-c',
                'import json; import gaap_backend.railway_settings as s; '
                'print(json.dumps([s.DEBUG, s.ALLOWED_HOSTS, s.CSRF_TRUSTED_ORIGINS, '
                'str(s.DATABASES["default"]["NAME"])]))',
            ],
            env=env,
            capture_output=True,
            text=True,
        )

    def test_requires_secret_key(self):
        result = self.run_settings()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SECRET_KEY environment variable is required', result.stderr)

    def test_uses_railway_settings_and_ephemeral_database(self):
        result = self.run_settings(
            SECRET_KEY='test-secret',
            ALLOWED_HOSTS='example.up.railway.app',
            CSRF_TRUSTED_ORIGINS='https://example.up.railway.app',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            [
                False,
                ['example.up.railway.app', '127.0.0.1'],
                ['https://example.up.railway.app'],
                '/tmp/gaap.sqlite3',
            ],
        )

    def test_rejects_empty_allowed_hosts(self):
        result = self.run_settings(
            SECRET_KEY='test-secret',
            ALLOWED_HOSTS=', ,',
            CSRF_TRUSTED_ORIGINS='https://example.up.railway.app',
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ALLOWED_HOSTS must contain at least one host', result.stderr)

    def test_requires_csrf_origin(self):
        result = self.run_settings(
            SECRET_KEY='test-secret',
            ALLOWED_HOSTS='example.up.railway.app',
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('CSRF_TRUSTED_ORIGINS environment variable is required', result.stderr)

    @patch('gaap.page_views.urllib_request.urlopen')
    @patch.dict(os.environ, {'PORT': '4567'})
    def test_internal_api_uses_railway_port(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.status = 200
        response.read.return_value = b'{"ok": true}'

        status, body = _api_call('GET', 'servicos/')

        self.assertEqual((status, body), (200, {'ok': True}))
        self.assertEqual(
            urlopen.call_args.args[0].full_url,
            'http://127.0.0.1:4567/api/v1/servicos/',
        )


class RailwayStaticTests(TestCase):
    def test_collected_admin_static_file_is_served(self):
        with tempfile.TemporaryDirectory() as static_root:
            with override_settings(
                DEBUG=False,
                STATIC_ROOT=static_root,
                STATIC_URL='/static/',
                MIDDLEWARE=['whitenoise.middleware.WhiteNoiseMiddleware'],
                ALLOWED_HOSTS=['testserver'],
            ):
                call_command('collectstatic', interactive=False, verbosity=0)
                response = Client().get('/static/admin/css/base.css')
                try:
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response['Content-Type'].startswith('text/css'))
                finally:
                    response.close()


class InternalApiLiveTests(LiveServerTestCase):
    @override_settings(ALLOWED_HOSTS=['127.0.0.1', 'localhost', 'testserver'])
    def test_token_and_authenticated_api_use_dynamic_port(self):
        perfil = Perfil.objects.create(codigo='ADMIN', nome='Administrador')
        get_user_model().objects.create_user(
            username='deployment-test', password='test-password', perfil=perfil
        )
        port = str(urlparse(self.live_server_url).port)
        with patch.dict(os.environ, {'PORT': port}):
            status, tokens = _api_call(
                'POST', 'auth/token/',
                {'username': 'deployment-test', 'password': 'test-password'},
            )
            self.assertEqual(status, 200)
            request = SimpleNamespace(session={'access_token': tokens['access']})
            status, body = _api_call('GET', 'servicos/', request=request)
        self.assertEqual(status, 200)
        self.assertEqual(body, [])
