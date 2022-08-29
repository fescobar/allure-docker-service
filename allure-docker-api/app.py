#pylint: disable=too-many-lines
from logging.config import dictConfig
from functools import wraps
from subprocess import call
import base64
import datetime
import glob
import io
import json
import os
import re
import shutil
import tempfile
import subprocess
import zipfile
import waitress
from werkzeug.utils import secure_filename
from flask import (
    Flask, jsonify, render_template, redirect,
    request, send_file, send_from_directory, make_response, url_for
)
from flask.logging import create_logger
from flask_swagger_ui import get_swaggerui_blueprint
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, create_refresh_token, current_user,
    get_jwt_identity, verify_jwt_in_request, jwt_refresh_token_required, get_raw_jwt,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies, verify_jwt_refresh_token_in_request
)

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(levelname)s] %(pathname)s:%(lineno)d %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

class UserAccess:
    """Object used for determining roles"""
    def __init__(self, username, roles):
        """
        :param username: username
        :param roles: roles
        """
        self.username = username
        self.roles = roles

    def get_username(self):
        return self.username

    def get_roles(self):
        return self.roles

    def __str__(self):
        return self.__class__.__name__

app = Flask(__name__) #pylint: disable=invalid-name

LOGGER = create_logger(app)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = False

DEV_MODE = 0
HOST = '0.0.0.0'
PORT = os.environ['PORT']
THREADS = 7
URL_SCHEME = 'http'
URL_PREFIX = ''
OPTIMIZE_STORAGE = 0
ENABLE_SECURITY_LOGIN = False
MAKE_VIEWER_ENDPOINTS_PUBLIC = False
SECURITY_USER = None
SECURITY_PASS = None
SECURITY_VIEWER_USER = None
SECURITY_VIEWER_PASS = None
USERS_INFO = {}
ADMIN_ROLE_NAME = 'admin'
VIEWER_ROLE_NAME = 'viewer'
PROTECTED_ENDPOINTS = [
    {
        "method": "post",
        "path": "/refresh",
        "endpoint": "refresh_endpoint"
    },
    {
        "method": "delete",
        "path": "/logout",
        "endpoint": "logout_endpoint"
    },
    {
        "method": "delete",
        "path": "/logout-refresh-token",
        "endpoint": "logout_refresh_token_endpoint"
    },
    {
        "method": "post",
        "path": "/send-results",
        "endpoint": "send_results_endpoint"
    },
    {
        "method": "get",
        "path": "/generate-report",
        "endpoint": "generate_report_endpoint"
    },
    {
        "method": "get",
        "path": "/clean-results",
        "endpoint": "clean_results_endpoint"
    },
    {
        "method": "get",
        "path": "/clean-history",
        "endpoint": "clean_history_endpoint"
    },
    {
        "method": "post",
        "path": "/projects",
        "endpoint": "create_project_endpoint"
    },
    {
        "method": "delete",
        "path": "/projects/{id}",
        "endpoint": "delete_project_endpoint"
    }
]

GENERATE_REPORT_PROCESS = '{}/generateAllureReport.sh'.format(os.environ['ROOT'])
KEEP_HISTORY_PROCESS = '{}/keepAllureHistory.sh'.format(os.environ['ROOT'])
CLEAN_HISTORY_PROCESS = '{}/cleanAllureHistory.sh'.format(os.environ['ROOT'])
CLEAN_RESULTS_PROCESS = '{}/cleanAllureResults.sh'.format(os.environ['ROOT'])
RENDER_EMAIL_REPORT_PROCESS = '{}/renderEmailableReport.sh'.format(os.environ['ROOT'])
ALLURE_VERSION = os.environ['ALLURE_VERSION']
STATIC_CONTENT = os.environ['STATIC_CONTENT']
PROJECTS_DIRECTORY = os.environ['STATIC_CONTENT_PROJECTS']
EMAILABLE_REPORT_FILE_NAME = os.environ['EMAILABLE_REPORT_FILE_NAME']
ORIGIN = 'api'
SECURITY_SPECS_PATH = 'swagger/security_specs'

REPORT_INDEX_FILE = 'index.html'
DEFAULT_TEMPLATE = 'default.html'
LANGUAGE_TEMPLATE = 'select_language.html'
LANGUAGES = ["en", "ru", "zh", "de", "nl", "he", "br", "pl", "ja", "es", "kr", "fr"]
GLOBAL_CSS = "https://stackpath.bootstrapcdn.com/bootswatch/4.3.1/cosmo/bootstrap.css"
EMAILABLE_REPORT_CSS = GLOBAL_CSS
EMAILABLE_REPORT_TITLE = "Emailable Report"
API_RESPONSE_LESS_VERBOSE = 0

if "EMAILABLE_REPORT_CSS_CDN" in os.environ:
    EMAILABLE_REPORT_CSS = os.environ['EMAILABLE_REPORT_CSS_CDN']
    LOGGER.info('Overriding CSS for Emailable Report. EMAILABLE_REPORT_CSS_CDN=%s',
                EMAILABLE_REPORT_CSS)

if "EMAILABLE_REPORT_TITLE" in os.environ:
    EMAILABLE_REPORT_TITLE = os.environ['EMAILABLE_REPORT_TITLE']
    LOGGER.info('Overriding Title for Emailable Report. EMAILABLE_REPORT_TITLE=%s',
                EMAILABLE_REPORT_TITLE)

if "API_RESPONSE_LESS_VERBOSE" in os.environ:
    try:
        API_RESPONSE_LESS_VERBOSE_TMP = int(os.environ['API_RESPONSE_LESS_VERBOSE'])
        if API_RESPONSE_LESS_VERBOSE_TMP in (1, 0):
            API_RESPONSE_LESS_VERBOSE = API_RESPONSE_LESS_VERBOSE_TMP
            LOGGER.info('Overriding API_RESPONSE_LESS_VERBOSE=%s', API_RESPONSE_LESS_VERBOSE)
        else:
            LOGGER.error('Wrong env var value. Setting API_RESPONSE_LESS_VERBOSE=0 by default')
    except Exception as ex:
        LOGGER.error('Wrong env var value. Setting API_RESPONSE_LESS_VERBOSE=0 by default')

if "DEV_MODE" in os.environ:
    try:
        DEV_MODE_TMP = int(os.environ['DEV_MODE'])
        if DEV_MODE_TMP in (1, 0):
            DEV_MODE = DEV_MODE_TMP
            LOGGER.info('Overriding DEV_MODE=%s', DEV_MODE)
        else:
            LOGGER.error('Wrong env var value. Setting DEV_MODE=0 by default')
    except Exception as ex:
        LOGGER.error('Wrong env var value. Setting DEV_MODE=0 by default')

if "TLS" in os.environ:
    try:
        IS_ITLS = int(os.environ['TLS'])
        if IS_ITLS == 1:
            URL_SCHEME = 'https'
            app.config['JWT_COOKIE_SECURE'] = True
            LOGGER.info('Enabling TLS=%s', IS_ITLS)
    except Exception as ex:
        LOGGER.error('Wrong env var value. Setting TLS=0 by default')

if "URL_PREFIX" in os.environ:
    PREFIX = str(os.environ['URL_PREFIX'])
    if DEV_MODE == 1:
        LOGGER.warning('URL_PREFIX is not supported when DEV_MODE is enabled')
    else:
        if PREFIX and PREFIX.strip():
            if PREFIX.startswith('/') is False:
                LOGGER.info('Adding slash at the beginning of URL_PREFIX')
                PREFIX = '/{}'.format(''.join(PREFIX))
            URL_PREFIX = PREFIX
            LOGGER.info('Setting URL_PREFIX=%s', URL_PREFIX)
        else:
            LOGGER.info("URL_PREFIX is empty. It won't be applied")

if "OPTIMIZE_STORAGE" in os.environ:
    try:
        OPTIMIZE_STORAGE_TMP = int(os.environ['OPTIMIZE_STORAGE'])
        if OPTIMIZE_STORAGE_TMP in (1, 0):
            OPTIMIZE_STORAGE = OPTIMIZE_STORAGE_TMP
            LOGGER.info('Overriding OPTIMIZE_STORAGE=%s', OPTIMIZE_STORAGE)
        else:
            LOGGER.error('Wrong env var value. Setting OPTIMIZE_STORAGE=0 by default')
    except Exception as ex:
        LOGGER.error('Wrong env var value. Setting OPTIMIZE_STORAGE=0 by default')

if "MAKE_VIEWER_ENDPOINTS_PUBLIC" in os.environ:
    try:
        VIEWER_ENDPOINTS_PUBLIC_TMP = int(os.environ['MAKE_VIEWER_ENDPOINTS_PUBLIC'])
        if VIEWER_ENDPOINTS_PUBLIC_TMP == 1:
            MAKE_VIEWER_ENDPOINTS_PUBLIC = True
            LOGGER.info('Overriding MAKE_VIEWER_ENDPOINTS_PUBLIC=%s', VIEWER_ENDPOINTS_PUBLIC_TMP)
    except Exception as ex:
        LOGGER.error('Wrong env var value. Setting VIEWER_ENDPOINTS_PUBLIC=0 by default')

if "JWT_SECRET_KEY" in os.environ:
    app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
else:
    app.config['JWT_SECRET_KEY'] = os.urandom(16)

if "SECURITY_USER" in os.environ:
    SECURITY_USER_TMP = os.environ['SECURITY_USER']
    if SECURITY_USER_TMP and SECURITY_USER_TMP.strip():
        SECURITY_USER = SECURITY_USER_TMP.lower()
        LOGGER.info('Setting SECURITY_USER')

if "SECURITY_PASS" in os.environ:
    SECURITY_PASS_TMP = os.environ['SECURITY_PASS']
    if SECURITY_PASS_TMP and SECURITY_PASS_TMP.strip():
        SECURITY_PASS = SECURITY_PASS_TMP
        LOGGER.info('Setting SECURITY_PASS')

if MAKE_VIEWER_ENDPOINTS_PUBLIC is False:
    if "SECURITY_VIEWER_USER" in os.environ:
        SECURITY_VIEWER_USER_TMP = os.environ['SECURITY_VIEWER_USER']
        if SECURITY_VIEWER_USER_TMP and SECURITY_VIEWER_USER_TMP.strip():
            SECURITY_VIEWER_USER = SECURITY_VIEWER_USER_TMP.lower()
            LOGGER.info('Setting SECURITY_VIEWER_USER')

    if "SECURITY_VIEWER_PASS" in os.environ:
        SECURITY_VIEWER_PASS_TMP = os.environ['SECURITY_VIEWER_PASS']
        if SECURITY_VIEWER_PASS_TMP and SECURITY_VIEWER_PASS_TMP.strip():
            SECURITY_VIEWER_PASS = SECURITY_VIEWER_PASS_TMP
            LOGGER.info('Setting SECURITY_VIEWER_PASS')

if "SECURITY_ENABLED" in os.environ:
    try:
        ENABLE_SECURITY_LOGIN_TMP = int(os.environ['SECURITY_ENABLED'])
        if SECURITY_USER and SECURITY_PASS:
            if SECURITY_USER != SECURITY_VIEWER_USER:
                if ENABLE_SECURITY_LOGIN_TMP == 1:
                    ENABLE_SECURITY_LOGIN = True
                    LOGGER.info('Enabling Security Login. SECURITY_ENABLED=1')
                    USERS_INFO[SECURITY_USER] = {
                                                    'pass': SECURITY_PASS,
                                                    'roles': [ADMIN_ROLE_NAME]
                                                }
                    if SECURITY_VIEWER_USER is not None and SECURITY_VIEWER_PASS is not None:
                        USERS_INFO[SECURITY_VIEWER_USER] = {
                                                                'pass': SECURITY_VIEWER_PASS,
                                                                'roles': [VIEWER_ROLE_NAME]
                                                           }
                else:
                    LOGGER.info('Setting SECURITY_ENABLED=0 by default')
            else:
                LOGGER.info('SECURITY_USER and SECURITY_VIEWER_USER should be different')
                LOGGER.info('Setting SECURITY_ENABLED=0 by default')
        else:
            LOGGER.info("To enable security you need SECURITY_USER' & 'SECURITY_PASS' env vars")
            LOGGER.info('Setting SECURITY_ENABLED=0 by default')
    except Exception as ex:
        LOGGER.error('Wrong env var value. Setting SECURITY_ENABLED=0 by default')
else:
    LOGGER.info('Setting SECURITY_ENABLED=0 by default')

# For development purposes
if "ACCESS_TOKEN_EXPIRES_IN_SECONDS" in os.environ:
    try:
        ACCESS_TOKEN_EXPIRES_IN_SECONDS = int(os.environ['ACCESS_TOKEN_EXPIRES_IN_SECONDS'])
        if ACCESS_TOKEN_EXPIRES_IN_SECONDS > 0:
            SECONDS = datetime.timedelta(seconds=ACCESS_TOKEN_EXPIRES_IN_SECONDS)
            app.config['JWT_ACCESS_TOKEN_EXPIRES'] = SECONDS
            LOGGER.info('Setting ACCESS_TOKEN_EXPIRES_IN_SECONDS=%s',
                        ACCESS_TOKEN_EXPIRES_IN_SECONDS)
        else:
            app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False
            LOGGER.info('Disabling ACCESS_TOKEN expiration')
    except Exception as ex:
        LOGGER.error('Wrong env var value. Setting ACCESS_TOKEN_EXPIRES_IN_DAYS by default 15 mins')

# For development purposes
if "REFRESH_TOKEN_EXPIRES_IN_SECONDS" in os.environ:
    try:
        REFRESH_TOKEN_EXPIRES_IN_SECONDS = int(os.environ['REFRESH_TOKEN_EXPIRES_IN_SECONDS'])
        if REFRESH_TOKEN_EXPIRES_IN_SECONDS > 0:
            SECONDS = datetime.timedelta(seconds=REFRESH_TOKEN_EXPIRES_IN_SECONDS)
            app.config['JWT_REFRESH_TOKEN_EXPIRES'] = SECONDS
            LOGGER.info('Setting REFRESH_TOKEN_EXPIRES_IN_SECONDS=%s',
                        REFRESH_TOKEN_EXPIRES_IN_SECONDS)
        else:
            app.config['JWT_REFRESH_TOKEN_EXPIRES'] = False
            LOGGER.info('Disabling REFRESH_TOKEN expiration')
    except Exception as ex:
        LOGGER.error('Wrong env var value. Setting REFRESH_TOKEN_EXPIRES_IN_SECONDS keeps disabled')

if "ACCESS_TOKEN_EXPIRES_IN_MINS" in os.environ:
    try:
        ACCESS_TOKEN_EXPIRES_IN_MINS = int(os.environ['ACCESS_TOKEN_EXPIRES_IN_MINS'])
        if ACCESS_TOKEN_EXPIRES_IN_MINS > 0:
            MINS = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRES_IN_MINS)
            app.config['JWT_ACCESS_TOKEN_EXPIRES'] = MINS
            LOGGER.info('Setting ACCESS_TOKEN_EXPIRES_IN_MINS=%s', ACCESS_TOKEN_EXPIRES_IN_MINS)
        else:
            app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False
            LOGGER.info('Disabling ACCESS_TOKEN expiration')
    except Exception as ex:
        LOGGER.error('Wrong env var value. Setting ACCESS_TOKEN_EXPIRES_IN_MINS by default 15 mins')

if "REFRESH_TOKEN_EXPIRES_IN_DAYS" in os.environ:
    try:
        REFRESH_TOKEN_EXPIRES_IN_DAYS = int(os.environ['REFRESH_TOKEN_EXPIRES_IN_DAYS'])
        if REFRESH_TOKEN_EXPIRES_IN_DAYS > 0:
            DAYS = datetime.timedelta(days=REFRESH_TOKEN_EXPIRES_IN_DAYS)
            app.config['JWT_REFRESH_TOKEN_EXPIRES'] = DAYS
            LOGGER.info('Setting REFRESH_TOKEN_EXPIRES_IN_DAYS=%s', REFRESH_TOKEN_EXPIRES_IN_DAYS)
        else:
            app.config['JWT_REFRESH_TOKEN_EXPIRES'] = False
            LOGGER.info('Disabling REFRESH_TOKEN expiration')
    except Exception as ex:
        LOGGER.error('Wrong env var value. Setting REFRESH_TOKEN_EXPIRES_IN_DAYS keeps disabled')

def get_file_as_string(path_file):
    file = None
    content = None
    try:
        file = open(path_file, "r")
        content = file.read()
    finally:
        if file is not None:
            file.close()
    return content

def get_security_specs():
    security_specs = {}
    for file in os.listdir("{}/{}/".format(STATIC_CONTENT, SECURITY_SPECS_PATH)):
        file_path = "{}/{}/{}".format(STATIC_CONTENT, SECURITY_SPECS_PATH, file)
        security_specs[file] = eval(get_file_as_string(file_path)) #pylint: disable=eval-used
    return security_specs

def is_endpoint_protected(endpoint):
    if MAKE_VIEWER_ENDPOINTS_PUBLIC is False:
        return True

    for info in PROTECTED_ENDPOINTS:
        if endpoint == info['endpoint']:
            return True
    return False

def is_endpoint_swagger_protected(method, path):
    if MAKE_VIEWER_ENDPOINTS_PUBLIC is False:
        return True

    for info in PROTECTED_ENDPOINTS:
        if info['method'] == method and path == info['path']:
            return True
    return False

def generate_security_swagger_spec():
    try:
        security_specs = get_security_specs()
        with open("{}/swagger/swagger.json".format(STATIC_CONTENT)) as json_file:
            data = json.load(json_file)
            data['tags'].insert(1, security_specs['security_tags.json'])
            data['paths']['/login'] = security_specs['login_spec.json']
            data['paths']['/refresh'] = security_specs['refresh_spec.json']
            data['paths']['/logout'] = security_specs['logout_spec.json']
            data['paths']['/logout-refresh-token'] = security_specs['logout_refresh_spec.json']
            data['components']['schemas']['login'] = security_specs['login_scheme.json']

            ensure_tags = ['Action', 'Project']
            security_type = security_specs['security_type.json']
            security_401_response = security_specs['security_unauthorized_response.json']
            security_403_response = security_specs['security_forbidden_response.json']
            security_crsf = security_specs['security_csrf.json']
            for path in data['paths']: #pylint: disable=too-many-nested-blocks
                for method in data['paths'][path]:
                    if is_endpoint_swagger_protected(method, path):
                        if set(ensure_tags) & set(data['paths'][path][method]['tags']):
                            data['paths'][path][method]['security'] = security_type
                            data['paths'][path][method]['responses']['401'] = security_401_response
                            data['paths'][path][method]['responses']['403'] = security_403_response
                            if method in ['post', 'put', 'patch', 'delete']:
                                if 'parameters' in data['paths'][path][method]:
                                    params = data['paths'][path][method]['parameters']
                                    params.append(security_crsf)
                                    data['paths'][path][method]['parameters'] = params
                                else:
                                    data['paths'][path][method]['parameters'] = [security_crsf]
        with open("{}/swagger/swagger_security.json".format(STATIC_CONTENT), 'w') as outfile:
            json.dump(data, outfile)
    except Exception as ex:
        LOGGER.error(str(ex))

### swagger specific ###
NATIVE_PREFIX = '/allure-docker-service'
SWAGGER_ENDPOINT = '/swagger'
SWAGGER_SPEC_FILE = '/swagger.json'

SWAGGER_ENDPOINT_PATH = '{}{}'.format(NATIVE_PREFIX, SWAGGER_ENDPOINT)
SWAGGER_SPEC = '{}{}'.format(NATIVE_PREFIX, SWAGGER_SPEC_FILE)

if URL_PREFIX:
    SWAGGER_ENDPOINT_PATH = '{}{}{}'.format(URL_PREFIX, NATIVE_PREFIX, SWAGGER_ENDPOINT)
    SWAGGER_SPEC = '{}{}{}'.format(URL_PREFIX, NATIVE_PREFIX, SWAGGER_SPEC_FILE)

SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    base_url=SWAGGER_ENDPOINT_PATH,
    api_url=SWAGGER_SPEC,
    config={
        'app_name': "Allure Docker Service"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix="/")
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=NATIVE_PREFIX)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_ENDPOINT)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_ENDPOINT_PATH)
if URL_PREFIX:
    app.register_blueprint(SWAGGERUI_BLUEPRINT,
        url_prefix='{}{}'.format(NATIVE_PREFIX, SWAGGER_ENDPOINT))
### end swagger specific ###

### Security Section
if ENABLE_SECURITY_LOGIN:
    generate_security_swagger_spec()

blacklist = set() #pylint: disable=invalid-name
jwt = JWTManager(app) #pylint: disable=invalid-name

@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return jti in blacklist

@jwt.invalid_token_loader
def invalid_token_loader(msg):
    return jsonify({
        'meta_data': {
            'message': 'Invalid Token - {}'.format(msg)
        }
    }), 401

@jwt.unauthorized_loader
def unauthorized_loader(msg):
    return jsonify({
        'meta_data': {
            'message': msg
        }
    }), 401

@jwt.expired_token_loader
def my_expired_token_callback(expired_token):
    token_type = expired_token['type']
    return jsonify({
        'meta_data': {
            'message': 'The {} token has expired'.format(token_type),
            'sub_status': 42,
        }
    }), 401

@jwt.revoked_token_loader
def revoked_token_loader():
    return jsonify({
        'meta_data': {
            'message': 'Revoked Token'
        }
    }), 401

def jwt_required(fn): #pylint: disable=invalid-name, function-redefined
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if ENABLE_SECURITY_LOGIN:
            if is_endpoint_protected(request.endpoint):
                verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper

def jwt_refresh_token_required(fn): #pylint: disable=invalid-name, function-redefined
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if ENABLE_SECURITY_LOGIN:
            if is_endpoint_protected(request.endpoint):
                verify_jwt_refresh_token_in_request()
        return fn(*args, **kwargs)
    return wrapper

@jwt.user_loader_callback_loader
def user_loader_callback(identity):
    if identity not in USERS_INFO:
        return None
    return UserAccess(
        username=identity,
        roles=USERS_INFO[identity]['roles']
    )
### end Security Section

### CORS section
@app.after_request
def after_request_func(response):
    origin = request.headers.get('Origin')
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Headers', 'x-csrf-token')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, OPTIONS, PUT, PATCH, DELETE')
        if origin:
            response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        if origin:
            response.headers.add('Access-Control-Allow-Origin', origin)

    return response
### end CORS section

### Security Endpoints Section
@app.route('/login', methods=['POST'], strict_slashes=False)
@app.route('/allure-docker-service/login', methods=['POST'], strict_slashes=False)
def login_endpoint():
    try:
        if ENABLE_SECURITY_LOGIN is False:
            body = {
                'meta_data': {
                    'message' : 'SECURITY is not enabled'
                }
            }
            resp = jsonify(body)
            return resp, 404

        content_type = str(request.content_type)
        if content_type is None and content_type.startswith('application/json') is False:
            raise Exception("Header 'Content-Type' must be 'application/json'")

        if not request.is_json:
            raise Exception("Missing JSON in body request")

        username = request.json.get('username', None)
        if not username:
            raise Exception("Missing 'username' attribute")
        username = username.lower()

        if username not in USERS_INFO:
            return jsonify({'meta_data': {'message' : 'Invalid username/password'}}), 401

        password = request.json.get('password', None)
        if not password:
            raise Exception("Missing 'password' attribute")

        if USERS_INFO[username]['pass'] != password:
            return jsonify({'meta_data': {'message' : 'Invalid username/password'}}), 401

        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        access_token_expires = app.config['JWT_ACCESS_TOKEN_EXPIRES']
        expires_in = access_token_expires.total_seconds() if access_token_expires else 0
        json_body = {
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': expires_in,
                'roles': USERS_INFO[username]['roles']
            },
            'meta_data': {'message' : 'Successfully logged'}
        }
        resp = jsonify(json_body)
        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)
        return resp, 200
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        return resp, 400

@app.route('/logout', methods=['DELETE'], strict_slashes=False)
@app.route('/allure-docker-service/logout', methods=['DELETE'], strict_slashes=False)
@jwt_required
def logout_endpoint():
    if ENABLE_SECURITY_LOGIN is False:
        body = {
            'meta_data': {
                'message' : 'SECURITY is not enabled'
            }
        }
        resp = jsonify(body)
        return resp, 404
    try:
        jti = get_raw_jwt()['jti']
        blacklist.add(jti)
        return jsonify({'meta_data': {'message' : 'Successfully logged out'}}), 200
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        return resp, 400

@app.route('/logout-refresh-token', methods=['DELETE'], strict_slashes=False)
@app.route('/allure-docker-service/logout-refresh-token', methods=['DELETE'], strict_slashes=False)
@jwt_refresh_token_required
def logout_refresh_token_endpoint():
    if ENABLE_SECURITY_LOGIN is False:
        body = {
            'meta_data': {
                'message' : 'SECURITY is not enabled'
            }
        }
        resp = jsonify(body)
        return resp, 404
    try:
        jti = get_raw_jwt()['jti']
        blacklist.add(jti)
        resp = jsonify({'meta_data': {'message' : 'Successfully logged out'}})
        unset_jwt_cookies(resp)
        return resp, 200
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        return resp, 400

@app.route('/refresh', methods=['POST'], strict_slashes=False)
@app.route('/allure-docker-service/refresh', methods=['POST'], strict_slashes=False)
@jwt_refresh_token_required
def refresh_endpoint():
    if ENABLE_SECURITY_LOGIN is False:
        body = {
            'meta_data': {
                'message' : 'SECURITY is not enabled'
            }
        }
        resp = jsonify(body)
        return resp, 404
    try:
        username = get_jwt_identity()
        access_token = create_access_token(identity=username)
        access_token_expires = app.config['JWT_ACCESS_TOKEN_EXPIRES']
        expires_in = access_token_expires.total_seconds() if access_token_expires else 0
        json_body = {
            'data': {
                'access_token': access_token,
                'expires_in': expires_in,
                'roles': USERS_INFO[username]['roles']
            },
            'meta_data': {
                'message' : 'Successfully token obtained'
            }
        }
        resp = jsonify(json_body)
        set_access_cookies(resp, access_token)
        return resp, 200
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        return resp, 400
### end Security Endpoints Section

@app.route("/swagger.json")
@app.route("/allure-docker-service/swagger.json", strict_slashes=False)
def swagger_json_endpoint():
    try:
        specification_file = 'swagger.json'
        if ENABLE_SECURITY_LOGIN:
            specification_file = 'swagger_security.json'

        if URL_PREFIX:
            spec = get_file_as_string("{}/swagger/{}".format(STATIC_CONTENT, specification_file))
            spec_json = eval(spec) #pylint: disable=eval-used
            server_url = spec_json['servers'][0]['url']
            spec_json['servers'][0]['url'] = '{}{}'.format(URL_PREFIX, server_url)
            return jsonify(spec_json)

        return send_file("{}/swagger/{}"
                         .format(STATIC_CONTENT, specification_file), mimetype='application/json')
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route("/version", strict_slashes=False)
@app.route("/allure-docker-service/version", strict_slashes=False)
def version_endpoint():
    try:
        version = get_file_as_string(ALLURE_VERSION).strip()
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        body = {
            'data': {
                'version': version
            },
            'meta_data': {
                'message' : "Version successfully obtained"
            }
        }
        resp = jsonify(body)
        resp.status_code = 200
    return resp

@app.route("/config", strict_slashes=False)
@app.route("/allure-docker-service/config", strict_slashes=False)
@jwt_required
def config_endpoint():
    try:
        version = get_file_as_string(ALLURE_VERSION).strip()
        check_results_every_seconds = os.getenv('CHECK_RESULTS_EVERY_SECONDS', '1')
        keep_history = os.getenv('KEEP_HISTORY', '0')
        keep_history_latest = os.getenv('KEEP_HISTORY_LATEST', '20')
        tls = int(app.config['JWT_COOKIE_SECURE'])
        security_enabled = int(ENABLE_SECURITY_LOGIN)
        make_viewer_endpoints_public = int(MAKE_VIEWER_ENDPOINTS_PUBLIC)

        body = {
            'data': {
                'version': version,
                'dev_mode': DEV_MODE,
                'check_results_every_seconds': check_results_every_seconds,
                'keep_history': keep_history,
                'keep_history_latest': keep_history_latest,
                'tls': tls,
                'security_enabled': security_enabled,
                'url_prefix': URL_PREFIX,
                'api_response_less_verbose': API_RESPONSE_LESS_VERBOSE,
                'optimize_storage': OPTIMIZE_STORAGE,
                "make_viewer_endpoints_public": make_viewer_endpoints_public
            },
            'meta_data': {
                'message' : "Config successfully obtained"
            }
        }
        resp = jsonify(body)
        resp.status_code = 200
        return resp
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route("/select-language", strict_slashes=False)
@app.route("/allure-docker-service/select-language", strict_slashes=False)
@jwt_required
def select_language_endpoint():
    try:
        code = request.args.get('code')
        if code is None:
            raise Exception("'code' query parameter is required")
        code = code.lower()

        if code not in LANGUAGES:
            raise Exception("'code' not supported. Use values: {}".format(LANGUAGES))

        return render_template(LANGUAGE_TEMPLATE, languageCode=code, css=GLOBAL_CSS)
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route("/latest-report", strict_slashes=False)
@app.route("/allure-docker-service/latest-report", strict_slashes=False)
@jwt_required
def latest_report_endpoint():
    try:
        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        project_report_latest_path = '/latest/{}'.format(REPORT_INDEX_FILE)
        url = url_for('get_reports_endpoint', project_id=project_id,
                      path=project_report_latest_path, redirect='false', _external=True)
        return redirect(url)
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route("/send-results", methods=['POST'], strict_slashes=False)
@app.route("/allure-docker-service/send-results", methods=['POST'], strict_slashes=False)
@jwt_required
def send_results_endpoint(): #pylint: disable=too-many-branches
    try:
        if check_admin_access(current_user) is False:
            return jsonify({ 'meta_data': { 'message': 'Access Forbidden' } }), 403

        content_type = str(request.content_type)
        if content_type is None:
            raise Exception("Header 'Content-Type' should start with 'application/json' or 'multipart/form-data'") #pylint: disable=line-too-long

        if (
                content_type.startswith('application/json') is False and
                content_type.startswith('multipart/form-data') is False
            ):
            raise Exception("Header 'Content-Type' should start with 'application/json' or 'multipart/form-data'") #pylint: disable=line-too-long

        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            if request.args.get('force_project_creation') == 'true':
                project_id = create_project({ "id": project_id })
            else:
                body = {
                    'meta_data': {
                        'message' : "project_id '{}' not found".format(project_id)
                    }
                }
                resp = jsonify(body)
                resp.status_code = 404
                return resp

        validated_results = []
        processed_files = []
        failed_files = []
        results_project = '{}/results'.format(get_project_path(project_id))

        if content_type.startswith('application/json') is True:
            json_body = request.get_json()

            if 'results' not in json_body:
                raise Exception("'results' array is required in the body")

            validated_results = validate_json_results(json_body['results'])
            send_json_results(results_project, validated_results, processed_files, failed_files)

        if content_type.startswith('multipart/form-data') is True:
            validated_results = validate_files_array(request.files.getlist('files[]'))
            send_files_results(results_project, validated_results, processed_files, failed_files)

        failed_files_count = len(failed_files)
        if failed_files_count > 0:
            raise Exception('Problems with files: {}'.format(failed_files))

        if API_RESPONSE_LESS_VERBOSE != 1:
            files = os.listdir(results_project)
            current_files_count = len(files)
            sent_files_count = len(validated_results)
            processed_files_count = len(processed_files)

    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        if API_RESPONSE_LESS_VERBOSE != 1:
            body = {
                'data': {
                    'current_files': files,
                    'current_files_count': current_files_count,
                    'failed_files': failed_files,
                    'failed_files_count': failed_files_count,
                    'processed_files': processed_files,
                    'processed_files_count': processed_files_count,
                    'sent_files_count': sent_files_count
                    },
                'meta_data': {
                    'message' : "Results successfully sent for project_id '{}'".format(project_id)
                }
            }
        else:
            body = {
                'meta_data': {
                    'message' : "Results successfully sent for project_id '{}'".format(project_id)
                }
            }

        resp = jsonify(body)
        resp.status_code = 200

    return resp

@app.route("/generate-report", strict_slashes=False)
@app.route("/allure-docker-service/generate-report", strict_slashes=False)
@jwt_required
def generate_report_endpoint():
    try:
        if check_admin_access(current_user) is False:
            return jsonify({ 'meta_data': { 'message': 'Access Forbidden' } }), 403

        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        files = None
        project_path = get_project_path(project_id)
        results_project = '{}/results'.format(project_path)

        if API_RESPONSE_LESS_VERBOSE != 1:
            files = os.listdir(results_project)

        execution_name = request.args.get('execution_name')
        if execution_name is None or not execution_name:
            execution_name = 'Execution On Demand'

        execution_from = request.args.get('execution_from')
        if execution_from is None or not execution_from:
            execution_from = ''

        execution_type = request.args.get('execution_type')
        if execution_type is None or not execution_type:
            execution_type = ''

        check_process(KEEP_HISTORY_PROCESS, project_id)
        check_process(GENERATE_REPORT_PROCESS, project_id)

        exec_store_results_process = '1'

        call([KEEP_HISTORY_PROCESS, project_id, ORIGIN])
        response = subprocess.Popen([
            GENERATE_REPORT_PROCESS, exec_store_results_process,
            project_id, ORIGIN, execution_name, execution_from, execution_type],
                                    stdout=subprocess.PIPE).communicate()[0]
        call([RENDER_EMAIL_REPORT_PROCESS, project_id, ORIGIN])

        build_order = 'latest'
        for line in response.decode("utf-8").split("\n"):
            if line.startswith("BUILD_ORDER"):
                build_order = line[line.index(':') + 1: len(line)]

        report_url = url_for('get_reports_endpoint', project_id=project_id,
                             path='{}/index.html'.format(build_order), _external=True)
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        if files is not None:
            body = {
                'data': {
                    'report_url': report_url,
                    'allure_results_files': files
                },
                'meta_data': {
                    'message' : "Report successfully generated for project_id '{}'"
                                .format(project_id)
                }
            }
        else:
            body = {
                'data': {
                    'report_url': report_url
                },
                'meta_data': {
                    'message' : "Report successfully generated for project_id '{}'"
                                .format(project_id)
                }
            }

        resp = jsonify(body)
        resp.status_code = 200

    return resp

@app.route("/clean-history", strict_slashes=False)
@app.route("/allure-docker-service/clean-history", strict_slashes=False)
@jwt_required
def clean_history_endpoint():
    try:
        if check_admin_access(current_user) is False:
            return jsonify({ 'meta_data': { 'message': 'Access Forbidden' } }), 403

        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        check_process(CLEAN_HISTORY_PROCESS, project_id)

        call([CLEAN_HISTORY_PROCESS, project_id, ORIGIN])
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        body = {
            'meta_data': {
                'message' : "History successfully cleaned for project_id '{}'".format(project_id)
            }
        }
        resp = jsonify(body)
        resp.status_code = 200

    return resp

@app.route("/clean-results", strict_slashes=False)
@app.route("/allure-docker-service/clean-results", strict_slashes=False)
@jwt_required
def clean_results_endpoint():
    try:
        if check_admin_access(current_user) is False:
            return jsonify({ 'meta_data': { 'message': 'Access Forbidden' } }), 403

        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        check_process(GENERATE_REPORT_PROCESS, project_id)
        check_process(CLEAN_RESULTS_PROCESS, project_id)

        call([CLEAN_RESULTS_PROCESS, project_id, ORIGIN])
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        body = {
            'meta_data': {
                'message' : "Results successfully cleaned for project_id '{}'".format(project_id)
            }
        }
        resp = jsonify(body)
        resp.status_code = 200

    return resp

@app.route("/emailable-report/render", strict_slashes=False)
@app.route("/allure-docker-service/emailable-report/render", strict_slashes=False)
@jwt_required
def emailable_report_render_endpoint():
    try:
        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        check_process(GENERATE_REPORT_PROCESS, project_id)

        project_path = get_project_path(project_id)
        tcs_latest_report_project = "{}/reports/latest/data/test-cases/*.json".format(project_path)

        files = glob.glob(tcs_latest_report_project)
        files.sort(key=os.path.getmtime, reverse=True)
        test_cases = []
        for file_name in files:
            with open(file_name) as file:
                json_string = file.read()
                LOGGER.debug("----TestCase-JSON----")
                LOGGER.debug(json_string)
                test_case = json.loads(json_string)
                if test_case["hidden"] is False:
                    test_cases.append(test_case)

        server_url = url_for('latest_report_endpoint', project_id=project_id, _external=True)

        if "SERVER_URL" in os.environ:
            server_url = os.environ['SERVER_URL']

        report = render_template(DEFAULT_TEMPLATE, css=EMAILABLE_REPORT_CSS,
                                 title=EMAILABLE_REPORT_TITLE, projectId=project_id,
                                 serverUrl=server_url, testCases=test_cases)

        emailable_report_path = '{}/reports/{}'.format(project_path, EMAILABLE_REPORT_FILE_NAME)
        file = None
        try:
            file = open(emailable_report_path, "w")
            file.write(report)
        finally:
            if file is not None:
                file.close()
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp
    else:
        return report

@app.route("/emailable-report/export", strict_slashes=False)
@app.route("/allure-docker-service/emailable-report/export", strict_slashes=False)
@jwt_required
def emailable_report_export_endpoint():
    try:
        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        check_process(GENERATE_REPORT_PROCESS, project_id)

        project_path = get_project_path(project_id)
        emailable_report_path = '{}/reports/{}'.format(project_path, EMAILABLE_REPORT_FILE_NAME)

        report = send_file(emailable_report_path, as_attachment=True)
    except Exception as ex:
        message = str(ex)

        body = {
            'meta_data': {
                'message' : message
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp
    else:
        return report

@app.route("/report/export", strict_slashes=False)
@app.route("/allure-docker-service/report/export", strict_slashes=False)
@jwt_required
def report_export_endpoint():
    try:
        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        check_process(GENERATE_REPORT_PROCESS, project_id)

        project_path = get_project_path(project_id)
        tmp_report = '{}/allure-report'.format(tempfile.mkdtemp())
        shutil.copytree('{}/reports/latest'.format(project_path), tmp_report)

        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as zipf:
            root_dir = os.path.basename(tmp_report)
            for dirpath, dirnames, files in os.walk(tmp_report): #pylint: disable=unused-variable
                for file in files:
                    file_path = os.path.join(dirpath, file)
                    parent_path = os.path.relpath(file_path, tmp_report)
                    zipf.write(file_path, os.path.join(root_dir, parent_path))
        data.seek(0)

        shutil.rmtree(tmp_report, ignore_errors=True)

        return send_file(
            data,
            mimetype='application/zip',
            as_attachment=True,
            attachment_filename='allure-docker-service-report.zip'
        )
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route("/projects", methods=['POST'], strict_slashes=False)
@app.route("/allure-docker-service/projects", methods=['POST'], strict_slashes=False)
@jwt_required
def create_project_endpoint():
    try:
        if check_admin_access(current_user) is False:
            return jsonify({ 'meta_data': { 'message': 'Access Forbidden' } }), 403

        if not request.is_json:
            raise Exception("Header 'Content-Type' is not 'application/json'")

        project_id = create_project(request.get_json())
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        body = {
            'data': {
                'id': project_id,
            },
            'meta_data': {
                'message' : "Project successfully created"
            }
        }
        resp = jsonify(body)
        resp.status_code = 201
    return resp

@app.route('/projects/<project_id>', methods=['DELETE'], strict_slashes=False)
@app.route("/allure-docker-service/projects/<project_id>", methods=['DELETE'], strict_slashes=False)
@jwt_required
def delete_project_endpoint(project_id):
    try:
        if check_admin_access(current_user) is False:
            return jsonify({ 'meta_data': { 'message': 'Access Forbidden' } }), 403

        if project_id == 'default':
            raise Exception("You must not remove project_id 'default'. Try with other projects")

        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        project_path = get_project_path(project_id)
        shutil.rmtree(project_path)
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        body = {
            'meta_data': {
                'message' : "project_id: '{}' successfully removed".format(project_id)
            }
        }
        resp = jsonify(body)
        resp.status_code = 200
    return resp

@app.route('/projects/<project_id>', strict_slashes=False)
@app.route("/allure-docker-service/projects/<project_id>", strict_slashes=False)
@jwt_required
def get_project_endpoint(project_id):
    try:
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        project_reports_path = '{}/reports'.format(get_project_path(project_id))
        reports_entity = []

        for file in os.listdir(project_reports_path):
            file_path = '{}/{}/index.html'.format(project_reports_path, file)
            is_file = os.path.isfile(file_path)
            if is_file is True:
                report = url_for('get_reports_endpoint', project_id=project_id,
                                 path='{}/index.html'.format(file), _external=True)
                reports_entity.append([report, os.path.getmtime(file_path), file])

        reports_entity.sort(key=lambda reports_entity: reports_entity[1], reverse=True)
        reports = []
        reports_id = []
        latest_report = None
        for report_entity in reports_entity:
            link = report_entity[0]
            if report_entity[2].lower() != 'latest':
                reports.append(link)
                reports_id.append(report_entity[2])
            else:
                latest_report = link

        if latest_report is not None:
            reports.insert(0, latest_report)
            reports_id.insert(0, 'latest')

        body = {
            'data': {
                'project': {
                    'id': project_id,
                    'reports': reports,
                    'reports_id': reports_id
                },
            },
            'meta_data': {
                'message' : "Project successfully obtained"
                }
            }
        resp = jsonify(body)
        resp.status_code = 200
        return resp
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route('/projects', strict_slashes=False)
@app.route("/allure-docker-service/projects", strict_slashes=False)
@jwt_required
def get_projects_endpoint():
    try:
        projects_dirs = os.listdir(PROJECTS_DIRECTORY)
        projects = get_projects(projects_dirs)

        body = {
            'data': {
                'projects': projects,
            },
            'meta_data': {
                'message' : "Projects successfully obtained"
                }
            }
        resp = jsonify(body)
        resp.status_code = 200
        return resp
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route('/projects/search', strict_slashes=False)
@app.route("/allure-docker-service/projects/search", strict_slashes=False)
@jwt_required
def get_projects_search_endpoint():
    try:
        project_id = request.args.get('id')
        if project_id is None:
            raise Exception("'id' query parameter is required")

        project_id = project_id.lower()
        projects_filtered = get_projects_filtered_by_id(project_id, os.listdir(PROJECTS_DIRECTORY))
        projects = get_projects(projects_filtered)

        if len(projects) == 0:
            return jsonify({'meta_data': {'message': 'Project not found'}}), 404

        body = {
            'data': {
                'projects': projects,
            },
            'meta_data': {
                'message' : "Project/s successfully obtained"
                }
            }
        resp = jsonify(body)
        resp.status_code = 200
        return resp
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route('/projects/<project_id>/reports/<path:path>')
@app.route("/allure-docker-service/projects/<project_id>/reports/<path:path>")
@jwt_required
def get_reports_endpoint(project_id, path):
    try:
        project_path = '{}/reports/{}'.format(project_id, path)
        return send_from_directory(PROJECTS_DIRECTORY, project_path)
    except Exception:
        if request.args.get('redirect') == 'false':
            return send_from_directory(PROJECTS_DIRECTORY, project_path)
        return redirect(url_for('get_project_endpoint', project_id=project_id, _external=True))


def validate_files_array(files):
    if not files:
        raise Exception("'files[]' array is empty")
    return files

def validate_json_results(results):
    if  isinstance(results, list) is False:
        raise Exception("'results' should be an array")

    if not results:
        raise Exception("'results' array is empty")

    map_results = {}
    for result in results:
        if 'file_name' not in result or not result['file_name'].strip():
            raise Exception("'file_name' attribute is required for all results")
        file_name = result.get('file_name')
        map_results[file_name] = ''

    if len(results) != len(map_results):
        raise Exception("Duplicated file names in 'results'")

    validated_results = []
    for result in results:
        file_name = result.get('file_name')
        validated_result = {}
        validated_result['file_name'] = file_name

        if 'content_base64' not in result or not result['content_base64'].strip():
            raise Exception("'content_base64' attribute is required for '{}' file"
                            .format(file_name))

        content_base64 = result.get('content_base64')
        try:
            validated_result['content_base64'] = base64.b64decode(content_base64)
        except Exception as ex:
            raise Exception(
                "'content_base64' attribute content for '{}' file should be encoded to base64"
                .format(file_name), ex)
        validated_results.append(validated_result)

    return validated_results

def send_files_results(results_project, validated_results, processed_files, failed_files):
    for file in validated_results:
        try:
            file_name = secure_filename(file.filename)
            file.save("{}/{}".format(results_project, file_name))
        except Exception as ex:
            error = {}
            error['message'] = str(ex)
            error['file_name'] = file_name
            failed_files.append(error)
        else:
            processed_files.append(file_name)

def send_json_results(results_project, validated_results, processed_files, failed_files):
    for result in validated_results:
        file_name = secure_filename(result.get('file_name'))
        content_base64 = result.get('content_base64')
        file = None
        try:
            file = open("%s/%s" % (results_project, file_name), "wb")
            file.write(content_base64)
        except Exception as ex:
            error = {}
            error['message'] = str(ex)
            error['file_name'] = file_name
            failed_files.append(error)
        else:
            processed_files.append(file_name)
        finally:
            if file is not None:
                file.close()

def create_project(json_body):
    if 'id' not in json_body:
        raise Exception("'id' is required in the body")

    if isinstance(json_body['id'], str) is False:
        raise Exception("'id' should be string")

    if not json_body['id'].strip():
        raise Exception("'id' should not be empty")

    if len(json_body['id']) > 100:
        raise Exception("'id' should not contains more than 100 characters.")

    project_id_pattern = re.compile('^[a-z\\d]([a-z\\d -]*[a-z\\d])?$')
    match = project_id_pattern.match(json_body['id'])
    if  match is None:
        raise Exception("'id' should contains alphanumeric lowercase characters or hyphens. For example: 'my-project-id'") #pylint: disable=line-too-long

    project_id = json_body['id']
    if is_existent_project(project_id) is True:
        raise Exception("project_id '{}' is existent".format(project_id))

    if project_id == 'default':
        raise Exception("The id 'default' is not allowed. Try with another project_id")

    project_path = get_project_path(project_id)
    latest_report_project = '{}/reports/latest'.format(project_path)
    results_project = '{}/results'.format(project_path)

    if not os.path.exists(latest_report_project):
        os.makedirs(latest_report_project)

    if not os.path.exists(results_project):
        os.makedirs(results_project)

    return project_id

def is_existent_project(project_id):
    if not project_id.strip():
        return False
    return os.path.isdir(get_project_path(project_id))

def get_projects(projects_dirs):
    projects = {}
    for project_name in projects_dirs:
        is_dir = os.path.isdir('{}/{}'.format(PROJECTS_DIRECTORY, project_name))
        if is_dir is True:
            project = {}
            project['uri'] = url_for('get_project_endpoint',
                                     project_id=project_name,
                                     _external=True)
            projects[project_name] = project
    return projects

def get_projects_filtered_by_id(project_id, projects):
    filtered_projects = []
    for project_name in projects:
        if project_id in project_name:
            filtered_projects.append(project_name)
    return filtered_projects

def get_project_path(project_id):
    return '{}/{}'.format(PROJECTS_DIRECTORY, project_id)

def resolve_project(project_id_param):
    project_id = 'default'
    if project_id_param is not None:
        project_id = project_id_param
    return project_id

def check_admin_access(user):
    if ENABLE_SECURITY_LOGIN is False:
        return True

    return check_access(ADMIN_ROLE_NAME, user)

def check_access(role, user):
    if user.roles is None:
        return False

    if role in user.roles:
        return True

    return False

def check_process(process_file, project_id):
    tmp = os.popen('ps -Af | grep -w {}'.format(project_id)).read()
    proccount = tmp.count(process_file)

    if proccount > 0:
        raise Exception("Processing files for project_id '{}'. Try later!".format(project_id))

if __name__ == '__main__':
    if DEV_MODE == 1:
        LOGGER.info('Starting in DEV_MODE')
        app.run(host=HOST, port=PORT)
    else:
        waitress.serve(app, threads=THREADS, host=HOST, port=PORT,
                       url_scheme=URL_SCHEME, url_prefix=URL_PREFIX)
