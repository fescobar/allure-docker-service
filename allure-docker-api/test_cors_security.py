import importlib
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from test_app import _setup_test_env


class CorsAndCookieSecurityTests(unittest.TestCase):
    """Tests for CORS origin allowlist enforcement and SameSite cookie attributes."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='allure-cors-test-')
        env = _setup_test_env(
            self.temp_dir,
            extra_env={
                'SECURITY_ENABLED': '1',
                'SECURITY_USER': 'admin',
                'SECURITY_PASS': 'secret-password-for-tests',
            },
        )
        self._patcher = patch.dict(os.environ, env, clear=True)
        self._patcher.start()
        self.addCleanup(self._patcher.stop)
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)

        import app as app_module  # pylint: disable=import-outside-toplevel
        self.app_module = importlib.reload(app_module)
        self.client = self.app_module.app.test_client()

    def test_default_denies_cross_origin_cors_headers(self):
        self.app_module.CORS_ALLOWED_ORIGINS = set()
        resp = self.client.get('/version', headers={'Origin': 'http://evil.example.com'})
        self.assertIsNone(resp.headers.get('Access-Control-Allow-Origin'))
        self.assertIsNone(resp.headers.get('Access-Control-Allow-Credentials'))

    def test_untrusted_origin_not_reflected_on_get_or_options(self):
        self.app_module.CORS_ALLOWED_ORIGINS = {'https://allure-ui.example.com'}
        for method in ('get', 'options'):
            resp = getattr(self.client, method)(
                '/version',
                headers={'Origin': 'https://evil.example.com'}
            )
            self.assertIsNone(resp.headers.get('Access-Control-Allow-Origin'))
            self.assertIsNone(resp.headers.get('Access-Control-Allow-Credentials'))

    def test_allowlisted_origin_receives_cors_headers_and_vary(self):
        self.app_module.CORS_ALLOWED_ORIGINS = self.app_module.parse_cors_allowed_origins(
            'http://localhost:7474/, *, https://allure-ui.example.com'
        )
        self.assertEqual(
            self.app_module.CORS_ALLOWED_ORIGINS,
            {'http://localhost:7474', 'https://allure-ui.example.com'}
        )

        get_resp = self.client.get('/version', headers={'Origin': 'http://localhost:7474'})
        self.assertEqual(
            get_resp.headers.get('Access-Control-Allow-Origin'),
            'http://localhost:7474'
        )
        self.assertEqual(get_resp.headers.get('Access-Control-Allow-Credentials'), 'true')
        self.assertIn('Origin', get_resp.headers.get('Vary', ''))

        opt_resp = self.client.options('/version', headers={'Origin': 'http://localhost:7474'})
        self.assertEqual(
            opt_resp.headers.get('Access-Control-Allow-Origin'),
            'http://localhost:7474'
        )
        self.assertEqual(opt_resp.headers.get('Access-Control-Allow-Credentials'), 'true')
        self.assertIn('x-csrf-token', opt_resp.headers.getlist('Access-Control-Allow-Headers'))

    def test_login_sets_samesite_lax_on_cookies(self):
        resp = self.client.post(
            '/allure-docker-service/login',
            json={'username': 'admin', 'password': 'secret-password-for-tests'}
        )
        self.assertEqual(resp.status_code, 200)
        set_cookies = resp.headers.getlist('Set-Cookie')
        self.assertTrue(
            any('access_token_cookie=' in c and 'SameSite=Lax' in c for c in set_cookies)
        )
        self.assertTrue(
            any('refresh_token_cookie=' in c and 'SameSite=Lax' in c for c in set_cookies)
        )


if __name__ == '__main__':
    unittest.main()
