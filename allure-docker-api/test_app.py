import base64
import importlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

REPO_API_DIR = os.path.dirname(os.path.abspath(__file__))
if REPO_API_DIR not in sys.path:
    sys.path.insert(0, REPO_API_DIR)


def _setup_test_env(temp_dir, extra_env=None):
    static_dir = os.path.join(temp_dir, 'static')
    projects_dir = os.path.join(static_dir, 'projects')
    default_dir = os.path.join(projects_dir, 'default')
    os.makedirs(os.path.join(default_dir, 'results'), exist_ok=True)
    os.makedirs(os.path.join(default_dir, 'reports', 'latest'), exist_ok=True)

    src_swagger = os.path.join(REPO_API_DIR, 'static', 'swagger')
    dst_swagger = os.path.join(static_dir, 'swagger')
    if os.path.exists(dst_swagger):
        shutil.rmtree(dst_swagger)
    shutil.copytree(src_swagger, dst_swagger)

    version_file = os.path.join(temp_dir, 'version')
    with open(version_file, 'w') as f_ver:
        f_ver.write('2.46.2\n')

    env = {
        'PORT': '5050',
        'ROOT': temp_dir,
        'ALLURE_VERSION': version_file,
        'STATIC_CONTENT': static_dir,
        'STATIC_CONTENT_PROJECTS': projects_dir,
        'EMAILABLE_REPORT_FILE_NAME': 'emailable-report-allure-docker-service.html',
        'JWT_SECRET_KEY': 'test-secret-key-for-unit-tests',
    }
    if extra_env:
        env.update(extra_env)
    return env


class TestAppHelpers(unittest.TestCase):
    """Unit tests for helper functions in app.py."""
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.env = _setup_test_env(cls.temp_dir)
        cls.env_patcher = patch.dict(os.environ, cls.env, clear=False)
        cls.env_patcher.start()
        import app as app_module  # pylint: disable=import-outside-toplevel
        cls.app_module = importlib.reload(app_module)

    @classmethod
    def tearDownClass(cls):
        cls.env_patcher.stop()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_user_access(self):
        user = self.app_module.UserAccess('alice', ['admin', 'viewer'])
        self.assertEqual(user.get_username(), 'alice')
        self.assertEqual(user.get_roles(), ['admin', 'viewer'])
        self.assertEqual(str(user), 'UserAccess')

    def test_get_file_as_string(self):
        content = self.app_module.get_file_as_string(self.env['ALLURE_VERSION'])
        self.assertEqual(content.strip(), '2.46.2')
        with self.assertRaises(FileNotFoundError):
            self.app_module.get_file_as_string(os.path.join(self.temp_dir, 'missing.txt'))

    def test_resolve_project_and_path(self):
        self.assertEqual(self.app_module.resolve_project(None), 'default')
        self.assertEqual(self.app_module.resolve_project('proj-1'), 'proj-1')
        expected = '{}/proj-1'.format(self.app_module.PROJECTS_DIRECTORY)
        self.assertEqual(self.app_module.get_project_path('proj-1'), expected)

    def test_is_existent_project(self):
        self.assertFalse(self.app_module.is_existent_project(''))
        self.assertFalse(self.app_module.is_existent_project('   '))
        self.assertFalse(self.app_module.is_existent_project('non-existent'))
        self.assertTrue(self.app_module.is_existent_project('default'))

    def test_get_projects_and_filter(self):
        # Create a file in PROJECTS_DIRECTORY to verify files are ignored
        marker_file = os.path.join(self.app_module.PROJECTS_DIRECTORY, 'not_a_dir.txt')
        with open(marker_file, 'w') as f_marker:
            f_marker.write('ignore')
        try:
            with self.app_module.app.test_request_context():
                projects = self.app_module.get_projects(['default', 'not_a_dir.txt'])
            self.assertIn('default', projects)
            self.assertNotIn('not_a_dir.txt', projects)
            self.assertIn('uri', projects['default'])
        finally:
            os.remove(marker_file)

        filtered = self.app_module.get_projects_filtered_by_id(
            'alpha', ['default', 'alpha-one', 'beta-alpha', 'gamma']
        )
        self.assertEqual(filtered, ['alpha-one', 'beta-alpha'])

    def test_check_access_and_admin(self):
        viewer = self.app_module.UserAccess('bob', ['viewer'])
        admin = self.app_module.UserAccess('alice', ['admin'])
        no_roles = self.app_module.UserAccess('nobody', None)

        self.assertFalse(self.app_module.check_access('admin', no_roles))
        self.assertFalse(self.app_module.check_access('admin', viewer))
        self.assertTrue(self.app_module.check_access('admin', admin))

        with patch.object(self.app_module, 'ENABLE_SECURITY_LOGIN', False):
            self.assertTrue(self.app_module.check_admin_access(viewer))

        with patch.object(self.app_module, 'ENABLE_SECURITY_LOGIN', True):
            self.assertFalse(self.app_module.check_admin_access(viewer))
            self.assertTrue(self.app_module.check_admin_access(admin))

    def test_is_endpoint_protected(self):
        with patch.object(self.app_module, 'MAKE_VIEWER_ENDPOINTS_PUBLIC', False):
            self.assertTrue(self.app_module.is_endpoint_protected('version_endpoint'))
            self.assertTrue(self.app_module.is_endpoint_swagger_protected('get', '/version'))

        with patch.object(self.app_module, 'MAKE_VIEWER_ENDPOINTS_PUBLIC', True):
            self.assertFalse(self.app_module.is_endpoint_protected('version_endpoint'))
            self.assertTrue(self.app_module.is_endpoint_protected('send_results_endpoint'))
            self.assertFalse(self.app_module.is_endpoint_swagger_protected('get', '/version'))
            self.assertTrue(
                self.app_module.is_endpoint_swagger_protected('post', '/send-results')
            )

    def test_validate_files_array(self):
        with self.assertRaises(Exception):
            self.app_module.validate_files_array([])
        mock_files = [MagicMock()]
        self.assertEqual(self.app_module.validate_files_array(mock_files), mock_files)

    def test_validate_json_results(self):
        with self.assertRaises(Exception):
            self.app_module.validate_json_results('not-a-list')
        with self.assertRaises(Exception):
            self.app_module.validate_json_results([])
        with self.assertRaises(Exception):
            self.app_module.validate_json_results([{'file_name': '  '}])
        with self.assertRaises(Exception):
            self.app_module.validate_json_results([
                {'file_name': 'a.json', 'content_base64': 'YQ=='},
                {'file_name': 'a.json', 'content_base64': 'Yg=='},
            ])
        with self.assertRaises(Exception):
            self.app_module.validate_json_results([{'file_name': 'a.json', 'content_base64': ' '}])
        with self.assertRaises(Exception):
            self.app_module.validate_json_results([{'file_name': 'a.json', 'content_base64': 'ab'}])

        encoded = base64.b64encode(b'hello').decode('utf-8')
        validated = self.app_module.validate_json_results([
            {'file_name': 'a.json', 'content_base64': encoded}
        ])
        self.assertEqual(validated, [{'file_name': 'a.json', 'content_base64': b'hello'}])

    def test_create_project_validation(self):
        for bad_body in [
            {},
            {'id': 123},
            {'id': '   '},
            {'id': 'a' * 101},
            {'id': 'InvalidUpper'},
            {'id': '-leading'},
            {'id': 'trailing-'},
            {'id': 'default'},
        ]:
            with self.assertRaises(Exception):
                self.app_module.create_project(bad_body)

        project_id = self.app_module.create_project({'id': 'valid-proj-1'})
        self.assertEqual(project_id, 'valid-proj-1')
        self.assertTrue(os.path.isdir(os.path.join(
            self.app_module.PROJECTS_DIRECTORY, 'valid-proj-1', 'results'
        )))
        self.assertTrue(os.path.isdir(os.path.join(
            self.app_module.PROJECTS_DIRECTORY, 'valid-proj-1', 'reports', 'latest'
        )))
        with self.assertRaises(Exception):
            self.app_module.create_project({'id': 'valid-proj-1'})

    def test_check_process(self):
        mock_popen = MagicMock()
        mock_popen.read.return_value = ''
        with patch.object(self.app_module.os, 'popen', return_value=mock_popen):
            self.app_module.check_process('generateAllureReport.sh', 'default')

        mock_popen.read.return_value = 'generateAllureReport.sh default'
        with patch.object(self.app_module.os, 'popen', return_value=mock_popen):
            with self.assertRaises(Exception):
                self.app_module.check_process('generateAllureReport.sh', 'default')


class TestAppEndpointsNoSecurity(unittest.TestCase):
    """Unit tests for HTTP endpoints with security disabled."""
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env = _setup_test_env(self.temp_dir)
        self.env_patcher = patch.dict(os.environ, self.env, clear=False)
        self.env_patcher.start()
        import app as app_module  # pylint: disable=import-outside-toplevel
        self.app_module = importlib.reload(app_module)
        self.client = self.app_module.app.test_client()

    def tearDown(self):
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cors_headers(self):
        resp_opt = self.client.options('/version', headers={'Origin': 'http://example.com'})
        self.assertEqual(resp_opt.status_code, 200)
        self.assertIsNone(resp_opt.headers.get('Access-Control-Allow-Origin'))
        self.assertIsNone(resp_opt.headers.get('Access-Control-Allow-Credentials'))

        resp_get = self.client.get('/version', headers={'Origin': 'http://example.com'})
        self.assertIsNone(resp_get.headers.get('Access-Control-Allow-Origin'))

        self.app_module.CORS_ALLOWED_ORIGINS = {'http://example.com'}
        resp_opt_allowed = self.client.options(
            '/version', headers={'Origin': 'http://example.com'}
        )
        self.assertEqual(resp_opt_allowed.status_code, 200)
        self.assertEqual(
            resp_opt_allowed.headers.get('Access-Control-Allow-Origin'),
            'http://example.com'
        )
        self.assertEqual(
            resp_opt_allowed.headers.get('Access-Control-Allow-Credentials'),
            'true'
        )

        resp_get_allowed = self.client.get('/version', headers={'Origin': 'http://example.com'})
        self.assertEqual(
            resp_get_allowed.headers.get('Access-Control-Allow-Origin'),
            'http://example.com'
        )

    def test_version_endpoint(self):
        resp = self.client.get('/version')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['data']['version'], '2.46.2')

        os.remove(self.env['ALLURE_VERSION'])
        resp_err = self.client.get('/allure-docker-service/version')
        self.assertEqual(resp_err.status_code, 400)

    def test_config_endpoint(self):
        resp = self.client.get('/config')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()['data']
        self.assertEqual(data['version'], '2.46.2')
        self.assertEqual(data['security_enabled'], 0)
        self.assertEqual(data['dev_mode'], 0)

        os.remove(self.env['ALLURE_VERSION'])
        resp_err = self.client.get('/config')
        self.assertEqual(resp_err.status_code, 400)

    def test_swagger_json_endpoint(self):
        resp = self.client.get('/swagger.json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('openapi', resp.get_json())

        with patch.object(self.app_module, 'URL_PREFIX', '/my-prefix'):
            resp_prefixed = self.client.get('/allure-docker-service/swagger.json')
            self.assertEqual(resp_prefixed.status_code, 200)
            server_url = resp_prefixed.get_json()['servers'][0]['url']
            self.assertTrue(server_url.startswith('/my-prefix'))

    def test_select_language_endpoint(self):
        resp_missing = self.client.get('/select-language')
        self.assertEqual(resp_missing.status_code, 400)

        resp_bad = self.client.get('/select-language?code=xx')
        self.assertEqual(resp_bad.status_code, 400)

        resp_ok = self.client.get('/select-language?code=EN')
        self.assertEqual(resp_ok.status_code, 200)
        self.assertIn(b'en', resp_ok.data)

    def test_latest_report_endpoint(self):
        resp_404 = self.client.get('/latest-report?project_id=missing')
        self.assertEqual(resp_404.status_code, 404)

        resp_302 = self.client.get('/latest-report?project_id=default')
        self.assertEqual(resp_302.status_code, 302)
        self.assertIn('/projects/default/reports/latest/index.html', resp_302.location)

    def test_projects_crud_and_search(self):
        # Create non-json -> 400
        resp_bad = self.client.post('/projects', data='not-json')
        self.assertEqual(resp_bad.status_code, 400)

        # Create valid -> 201
        resp_create = self.client.post('/projects', json={'id': 'my-proj'})
        self.assertEqual(resp_create.status_code, 201)
        self.assertEqual(resp_create.get_json()['data']['id'], 'my-proj')

        # List projects
        resp_list = self.client.get('/projects')
        self.assertEqual(resp_list.status_code, 200)
        projects = resp_list.get_json()['data']['projects']
        self.assertIn('default', projects)
        self.assertIn('my-proj', projects)

        # Search projects
        self.assertEqual(self.client.get('/projects/search').status_code, 400)
        self.assertEqual(self.client.get('/projects/search?id=nope').status_code, 404)
        resp_search = self.client.get('/projects/search?id=MY-PR')
        self.assertEqual(resp_search.status_code, 200)
        self.assertIn('my-proj', resp_search.get_json()['data']['projects'])

        # Get project with reports
        latest_idx = os.path.join(
            self.app_module.PROJECTS_DIRECTORY, 'my-proj', 'reports', 'latest', 'index.html'
        )
        build_dir = os.path.join(self.app_module.PROJECTS_DIRECTORY, 'my-proj', 'reports', '1')
        os.makedirs(build_dir, exist_ok=True)
        with open(latest_idx, 'w') as f_idx:
            f_idx.write('latest')
        with open(os.path.join(build_dir, 'index.html'), 'w') as f_b:
            f_b.write('build 1')

        self.assertEqual(self.client.get('/projects/unknown').status_code, 404)
        resp_get = self.client.get('/projects/my-proj')
        self.assertEqual(resp_get.status_code, 200)
        self.assertEqual(resp_get.get_json()['data']['project']['reports_id'], ['latest', '1'])

        # Get report file
        resp_report = self.client.get('/projects/my-proj/reports/latest/index.html')
        self.assertEqual(resp_report.status_code, 200)
        self.assertEqual(resp_report.data, b'latest')

        resp_missing_redir = self.client.get('/projects/my-proj/reports/missing.html')
        self.assertEqual(resp_missing_redir.status_code, 302)

        resp_missing_no_redir = self.client.get(
            '/projects/my-proj/reports/missing.html?redirect=false'
        )
        self.assertEqual(resp_missing_no_redir.status_code, 404)

        # Delete project
        self.assertEqual(self.client.delete('/projects/default').status_code, 400)
        self.assertEqual(self.client.delete('/projects/unknown').status_code, 404)
        self.assertEqual(self.client.delete('/projects/my-proj').status_code, 200)
        self.assertFalse(self.app_module.is_existent_project('my-proj'))

    def test_send_results_json_and_multipart(self):
        # Wrong content-type
        resp_ct = self.client.post('/send-results', data='raw', content_type='text/plain')
        self.assertEqual(resp_ct.status_code, 400)

        # Missing project without force_project_creation
        payload = {
            'results': [
                {
                    'file_name': 'test-result.json',
                    'content_base64': base64.b64encode(b'{"name":"t1"}').decode('utf-8'),
                }
            ]
        }
        resp_404 = self.client.post('/send-results?project_id=auto-proj', json=payload)
        self.assertEqual(resp_404.status_code, 404)

        # With force_project_creation=true
        resp_ok = self.client.post(
            '/send-results?project_id=auto-proj&force_project_creation=true',
            json=payload,
        )
        self.assertEqual(resp_ok.status_code, 200)
        data = resp_ok.get_json()['data']
        self.assertEqual(data['processed_files'], ['test-result.json'])
        self.assertEqual(data['sent_files_count'], 1)

        # Missing results key
        resp_no_key = self.client.post('/send-results', json={'wrong': []})
        self.assertEqual(resp_no_key.status_code, 400)

        # Multipart upload with API_RESPONSE_LESS_VERBOSE=1
        with patch.object(self.app_module, 'API_RESPONSE_LESS_VERBOSE', 1):
            resp_mp = self.client.post(
                '/send-results',
                data={'files[]': (io.BytesIO(b'content'), 'upload.txt')},
                content_type='multipart/form-data',
            )
            self.assertEqual(resp_mp.status_code, 200)
            self.assertNotIn('data', resp_mp.get_json())

    def test_generate_clean_and_emailable_endpoints(self):
        self.assertEqual(self.client.get('/generate-report?project_id=missing').status_code, 404)
        self.assertEqual(self.client.get('/clean-history?project_id=missing').status_code, 404)
        self.assertEqual(self.client.get('/clean-results?project_id=missing').status_code, 404)
        self.assertEqual(
            self.client.get('/emailable-report/render?project_id=missing').status_code, 404
        )
        self.assertEqual(
            self.client.get('/emailable-report/export?project_id=missing').status_code, 404
        )
        self.assertEqual(self.client.get('/report/export?project_id=missing').status_code, 404)

        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (b'BUILD_ORDER:7\n', b'')
        with patch.object(self.app_module, 'check_process'), \
             patch.object(self.app_module, 'call') as mock_call, \
             patch.object(self.app_module.subprocess, 'Popen', return_value=mock_proc):
            resp_gen = self.client.get('/generate-report?execution_name=CI')
            self.assertEqual(resp_gen.status_code, 200)
            self.assertIn('7/index.html', resp_gen.get_json()['data']['report_url'])
            self.assertEqual(mock_call.call_count, 2)

            resp_ch = self.client.get('/clean-history')
            self.assertEqual(resp_ch.status_code, 200)

            resp_cr = self.client.get('/clean-results')
            self.assertEqual(resp_cr.status_code, 200)

            # Emailable report render
            tc_dir = os.path.join(
                self.app_module.PROJECTS_DIRECTORY,
                'default',
                'reports',
                'latest',
                'data',
                'test-cases',
            )
            os.makedirs(tc_dir, exist_ok=True)
            with open(os.path.join(tc_dir, 'tc1.json'), 'w') as f_tc1:
                json.dump({'name': 'Visible TC', 'status': 'passed', 'hidden': False}, f_tc1)
            with open(os.path.join(tc_dir, 'tc2.json'), 'w') as f_tc2:
                json.dump({'name': 'Hidden TC', 'status': 'passed', 'hidden': True}, f_tc2)

            resp_render = self.client.get('/emailable-report/render')
            self.assertEqual(resp_render.status_code, 200)
            self.assertIn(b'Visible TC', resp_render.data)
            self.assertNotIn(b'Hidden TC', resp_render.data)

            # Emailable report export
            resp_export_email = self.client.get('/emailable-report/export')
            self.assertEqual(resp_export_email.status_code, 200)

            # Full report export as zip
            resp_export_zip = self.client.get('/report/export')
            self.assertEqual(resp_export_zip.status_code, 200)
            self.assertEqual(resp_export_zip.mimetype, 'application/zip')

    def test_security_endpoints_disabled(self):
        self.assertEqual(self.client.post('/login', json={}).status_code, 404)
        self.assertEqual(self.client.delete('/logout').status_code, 404)
        self.assertEqual(self.client.delete('/logout-refresh-token').status_code, 404)
        self.assertEqual(self.client.post('/refresh').status_code, 404)


class TestAppSecurityEnabled(unittest.TestCase):
    """Unit tests for JWT security and RBAC endpoints."""
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env = _setup_test_env(self.temp_dir, {
            'SECURITY_ENABLED': '1',
            'SECURITY_USER': 'admin',
            'SECURITY_PASS': 'adminpass',
            'SECURITY_VIEWER_USER': 'viewer',
            'SECURITY_VIEWER_PASS': 'viewerpass',
            'ACCESS_TOKEN_EXPIRES_IN_SECONDS': '60',
            'REFRESH_TOKEN_EXPIRES_IN_SECONDS': '120',
        })
        self.env_patcher = patch.dict(os.environ, self.env, clear=False)
        self.env_patcher.start()
        import app as app_module  # pylint: disable=import-outside-toplevel
        self.app_module = importlib.reload(app_module)
        self.client = self.app_module.app.test_client()

    def tearDown(self):
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _get_csrf_cookie(self, name):
        cookie = self.client.get_cookie(name)
        return cookie.value if cookie else ''

    def test_login_refresh_logout_and_rbac(self):
        # Missing JSON / invalid credentials
        self.assertEqual(self.client.post('/login', data='bad').status_code, 400)
        self.assertEqual(
            self.client.post('/login', json={'username': 'admin', 'password': 'wrong'}).status_code,
            401,
        )
        self.assertEqual(
            self.client.post('/login', json={'username': 'ghost', 'password': 'x'}).status_code,
            401,
        )

        # Unauthenticated access to protected viewer endpoint -> 401 (/version is always public)
        self.assertEqual(self.client.get('/version').status_code, 200)
        self.assertEqual(self.client.get('/config').status_code, 401)

        # Login as viewer
        resp_viewer = self.client.post(
            '/login', json={'username': 'viewer', 'password': 'viewerpass'}
        )
        self.assertEqual(resp_viewer.status_code, 200)
        self.assertEqual(resp_viewer.get_json()['data']['roles'], ['viewer'])

        # Viewer can read /config
        self.assertEqual(self.client.get('/config').status_code, 200)

        # Viewer forbidden on admin endpoint
        csrf_access = self._get_csrf_cookie('csrf_access_token')
        resp_forbidden = self.client.post(
            '/projects',
            json={'id': 'forbidden-proj'},
            headers={'X-CSRF-TOKEN': csrf_access},
        )
        self.assertEqual(resp_forbidden.status_code, 403)

        # Login as admin
        resp_admin = self.client.post(
            '/login', json={'username': 'admin', 'password': 'adminpass'}
        )
        self.assertEqual(resp_admin.status_code, 200)
        csrf_access = self._get_csrf_cookie('csrf_access_token')
        csrf_refresh = self._get_csrf_cookie('csrf_refresh_token')

        # Admin can create project
        resp_create = self.client.post(
            '/projects',
            json={'id': 'sec-proj'},
            headers={'X-CSRF-TOKEN': csrf_access},
        )
        self.assertEqual(resp_create.status_code, 201)

        # Refresh access token
        resp_refresh = self.client.post(
            '/refresh',
            headers={'X-CSRF-TOKEN': csrf_refresh},
        )
        self.assertEqual(resp_refresh.status_code, 200)
        self.assertIn('access_token', resp_refresh.get_json()['data'])
        csrf_access = self._get_csrf_cookie('csrf_access_token')

        # Logout revokes access token
        resp_logout = self.client.delete(
            '/logout',
            headers={'X-CSRF-TOKEN': csrf_access},
        )
        self.assertEqual(resp_logout.status_code, 200)
        self.assertEqual(self.client.get('/config').status_code, 401)

        # Logout refresh token revokes refresh token and unsets cookies
        resp_logout_ref = self.client.delete(
            '/logout-refresh-token',
            headers={'X-CSRF-TOKEN': csrf_refresh},
        )
        self.assertEqual(resp_logout_ref.status_code, 200)

    def test_make_viewer_endpoints_public(self):
        with patch.object(self.app_module, 'MAKE_VIEWER_ENDPOINTS_PUBLIC', True):
            self.assertEqual(self.client.get('/config').status_code, 200)
            self.assertEqual(self.client.get('/projects').status_code, 200)
            self.assertEqual(self.client.post('/projects', json={'id': 'p1'}).status_code, 401)


if __name__ == '__main__':
    unittest.main()
