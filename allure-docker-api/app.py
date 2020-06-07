from flask import Flask, jsonify, render_template, send_file, request, send_from_directory, redirect, url_for
from flask_swagger_ui import get_swaggerui_blueprint
from subprocess import call
from werkzeug.utils import secure_filename
import os, uuid, glob, json, base64, zipfile, io, re, shutil, tempfile

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

GENERATE_REPORT_PROCESS = '{}/generateAllureReport.sh'.format(os.environ['ROOT'])
KEEP_HISTORY_PROCESS = '{}/keepAllureHistory.sh'.format(os.environ['ROOT'])
CLEAN_HISTORY_PROCESS = '{}/cleanAllureHistory.sh'.format(os.environ['ROOT'])
CLEAN_RESULTS_PROCESS = '{}/cleanAllureResults.sh'.format(os.environ['ROOT'])
RENDER_EMAIL_REPORT_PROCESS = '{}/renderEmailableReport.sh'.format(os.environ['ROOT'])
ALLURE_VERSION = os.environ['ALLURE_VERSION']
PROJECTS_DIRECTORY = os.environ['STATIC_CONTENT_PROJECTS']
EMAILABLE_REPORT_FILE_NAME = os.environ['EMAILABLE_REPORT_FILE_NAME']
ORIGIN='api'

REPORT_INDEX_FILE = 'index.html'
DEFAULT_TEMPLATE = 'default.html'
CSS = "https://stackpath.bootstrapcdn.com/bootswatch/4.3.1/cosmo/bootstrap.css"
TITLE = "Emailable Report"
API_RESPONSE_LESS_VERBOSE = ''

if "EMAILABLE_REPORT_CSS_CDN" in os.environ:
    app.logger.info('Overriding CSS')
    CSS = os.environ['EMAILABLE_REPORT_CSS_CDN']

if "EMAILABLE_REPORT_TITLE" in os.environ:
    app.logger.info('Overriding Title')
    TITLE = os.environ['EMAILABLE_REPORT_TITLE']

if "API_RESPONSE_LESS_VERBOSE" in os.environ:
    API_RESPONSE_LESS_VERBOSE = os.environ['API_RESPONSE_LESS_VERBOSE']

### swagger specific ###
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config = {
        'app_name': "Allure Docker Service"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
### end swagger specific ###

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/version", strict_slashes=False)
def version():
    f = None
    try:
        f = open(ALLURE_VERSION, "r")
        version = f.read()
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
                'version': version.strip()
            },
            'meta_data': {
                'message' : "Version successfully obtained"
            }
        }
        resp = jsonify(body)
        resp.status_code = 200
    finally:
        if f is not None:
            f.close()

    return resp

@app.route("/latest-report", strict_slashes=False)
def latest_report():
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
        url = url_for('get_reports', project_id=project_id, path=project_report_latest_path, redirect='false', _external=True)
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
def send_results():
    try:
        content_type = request.content_type
        if content_type is None:
            raise Exception("Header 'Content-Type' should be 'application/json' or 'multipart/form-data'")

        if content_type != 'application/json' and content_type.startswith('multipart/form-data') is False:
            raise Exception("Header 'Content-Type' should be 'application/json' or 'multipart/form-data'")

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

        processedFiles = []
        failedFiles = []
        validatedResults = []
        project_path = get_project_path(project_id)
        results_project='{}/results'.format(project_path)

        if content_type == 'application/json':
            json = request.get_json()

            if 'results' not in json:
                raise Exception("'results' array is required in the body")

            results = json['results']

            if  isinstance(results, list) == False:
                raise Exception("'results' should be an array")

            if not results:
                raise Exception("'results' array is empty")

            map_results = {}
            for result in results:
                if 'file_name' not in result or not result['file_name'].strip():
                    raise Exception("'file_name' attribute is required for all results")
                fileName = result.get('file_name')
                map_results[fileName] = ''

            if len(results) != len(map_results):
                raise Exception("Duplicated file names in 'results'")

            for result in results:
                file_name = result.get('file_name')
                validated_result = {}
                validated_result['file_name'] = file_name

                if 'content_base64' not in result or not result['content_base64'].strip():
                    raise Exception("'content_base64' attribute is required for '%s' file" % (file_name))
                else:
                    content_base64 = result.get('content_base64')
                    try:
                        validated_result['content_base64'] = base64.b64decode(content_base64)
                    except Exception:
                        raise Exception("'content_base64' attribute content for '%s' file should be encoded to base64" % (file_name))

                validatedResults.append(validated_result)

            for result in validatedResults:
                file_name = secure_filename(result.get('file_name'))
                content_base64 = result.get('content_base64')
                f = None
                try:
                    f = open("%s/%s" % (results_project, file_name), "wb")
                    f.write(content_base64)
                except Exception as ex:
                    error = {}
                    error['message'] = str(ex)
                    error['file_name'] = file_name
                    failedFiles.append(error)
                else:
                    processedFiles.append(file_name)
                finally:
                    if f is not None:
                        f.close()

        if content_type.startswith('multipart/form-data') is True:
            files = request.files.getlist('files[]')
            if not files:
                raise Exception("'files[]' array is empty")

            for file in files:
                try:
                    file_name = secure_filename(file.filename)
                    file.save("{}/{}".format(results_project, file_name))
                except Exception as ex:
                    error = {}
                    error['message'] = str(ex)
                    error['file_name'] = file_name
                    failedFiles.append(error)
                else:
                    processedFiles.append(file_name)

            validatedResults = processedFiles


        failedFilesCount = len(failedFiles)
        if failedFilesCount > 0:
            raise Exception('Problems with files: {}'.format(failedFiles))

        if API_RESPONSE_LESS_VERBOSE != "1":
            files = os.listdir(results_project)
            currentFilesCount = len(files)
            sentFilesCount = len(validatedResults)
            processedFilesCount = len(processedFiles)

    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        if API_RESPONSE_LESS_VERBOSE != "1":
            body = {
                'data': {
                    'current_files': files,
                    'current_files_count': currentFilesCount,
                    'failed_files': failedFiles,
                    'failed_files_count': failedFilesCount,
                    'processed_files': processedFiles,
                    'processed_files_count': processedFilesCount,
                    'sent_files_count': sentFilesCount
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
def generate_report():
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

        files = None
        project_path=get_project_path(project_id)
        results_project='{}/results'.format(project_path)

        if API_RESPONSE_LESS_VERBOSE != "1":
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

        exec_store_results_process='1'

        call([KEEP_HISTORY_PROCESS, project_id, ORIGIN])
        call([GENERATE_REPORT_PROCESS, exec_store_results_process, project_id, ORIGIN, execution_name, execution_from, execution_type])
        call([RENDER_EMAIL_REPORT_PROCESS, project_id, ORIGIN])
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
                    'allure_results_files': files
                },
                'meta_data': {
                    'message' : "Report successfully generated for project_id '{}'".format(project_id)
                }
            }
        else:
            body = {
                'meta_data': {
                    'message' : "Report successfully generated for project_id '{}'".format(project_id)
                }
            }

        resp = jsonify(body)
        resp.status_code = 200

    return resp

@app.route("/clean-history", strict_slashes=False)
def clean_history():
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
def clean_results():
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
def emailable_report_render():
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

        project_path=get_project_path(project_id)
        tests_cases_latest_report_project='{}/reports/latest/data/test-cases/*.json'.format(project_path)

        files = glob.glob(tests_cases_latest_report_project)
        testCases = []
        for fileName in files:
            with open(fileName) as f:
                jsonString = f.read()
                app.logger.debug("----TestCase-JSON----")
                app.logger.debug(jsonString)
                testCase = json.loads(jsonString)
                if testCase["hidden"] is False:
                    testCases.append(testCase)

        server_url = url_for('latest_report', project_id=project_id, _external=True)

        if "SERVER_URL" in os.environ:
            app.logger.info('Overriding Allure Server Url')
            server_url = os.environ['SERVER_URL']

        report = render_template(DEFAULT_TEMPLATE, css=CSS, title=TITLE, projectId=project_id, serverUrl=server_url, testCases=testCases)

        emailable_report_path = '{}/reports/{}'.format(project_path, EMAILABLE_REPORT_FILE_NAME)
        f = None
        try:
            f = open(emailable_report_path, "w")
            f.write(report)
        finally:
            if f is not None:
                f.close()
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
def emailable_report_export():
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

        project_path=get_project_path(project_id)
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
def report_export():
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

        project_path=get_project_path(project_id)
        reports_project='{}/reports/latest'.format(project_path)

        tmp_dir = tempfile.mkdtemp()
        tmp_report = '{}/allure-report'.format(tmp_dir)
        shutil.copytree(reports_project, tmp_report)

        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as zipf:
            rootDir = os.path.basename(tmp_report)
            for dirpath, dirnames, files in os.walk(tmp_report):
                for file in files:
                    filePath = os.path.join(dirpath, file)
                    parentPath = os.path.relpath(filePath, tmp_report)
                    arcname = os.path.join(rootDir, parentPath)
                    zipf.write(filePath, arcname)
        data.seek(0)

        shutil.rmtree(tmp_report, ignore_errors=True)

        report = send_file(
            data,
            mimetype='application/zip',
            as_attachment=True,
            attachment_filename='allure-docker-service-report.zip'
        )
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

@app.route("/projects", methods=['POST'], strict_slashes=False)
def create_project():
    try:
        if not request.is_json:
            raise Exception("Header 'Content-Type' is not 'application/json'")

        json = request.get_json()

        if 'id' not in json:
            raise Exception("'id' is required in the body")

        if isinstance(json['id'], str) is False:
            raise Exception("'id' should be string")

        if not json['id'].strip():
            raise Exception("'id' should not be empty")

        project_id_pattern = re.compile('^[a-z\d]([a-z\d -]*[a-z\d])?$')
        match = project_id_pattern.match(json['id'])
        if  match is None:
            raise Exception("'id' should contains alphanumeric lowercase characters or hyphens. For example: 'my-project-id'")

        project_id = json['id']
        if is_existent_project(project_id) is True:
            raise Exception("project_id '{}' is existent".format(project_id))

        if project_id == 'default':
            raise Exception("The id 'default' is not allowed. Try with another project_id")

        project_path=get_project_path(project_id)
        latest_report_project='{}/reports/latest'.format(project_path)
        results_project='{}/results'.format(project_path)

        if not os.path.exists(latest_report_project):
            os.makedirs(latest_report_project)

        if not os.path.exists(results_project):
            os.makedirs(results_project)
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
def delete_project(project_id):
    try:
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

        project_path=get_project_path(project_id)
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
def get_project(project_id):
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

        directories = os.listdir(project_reports_path)
        for file in directories:
            file_path = '{}/{}/index.html'.format(project_reports_path, file)
            is_file = os.path.isfile(file_path)
            if is_file is True:
                report = url_for('get_reports', project_id=project_id, path='{}/index.html'.format(file), _external=True)
                reports_entity.append([report, os.path.getmtime(file_path), file])

        reports_entity.sort(key=lambda reports_entity:reports_entity[1], reverse=True)
        reports = []
        latest_report = None
        for report_entity in reports_entity:
            link = report_entity[0]
            if report_entity[2].lower() != 'latest':
                reports.append(link)
            else:
                latest_report = link

        if latest_report is not None:
            reports.insert(0, latest_report)

        body = {
            'data': {
                'project': {
                    'id': project_id,
                    'reports': reports
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
def get_projects():
    try:
        directories = os.listdir(PROJECTS_DIRECTORY)
        projects = {}
        for project_name in directories:
            is_dir = os.path.isdir('{}/{}'.format(PROJECTS_DIRECTORY, project_name))
            if is_dir is True:
                project = {}
                project['uri'] = url_for('get_project', project_id=project_name, _external=True)
                projects[project_name] = project

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

@app.route('/projects/<project_id>/reports/<path:path>')
def get_reports(project_id, path):
    try:
        project_path = '{}/reports/{}'.format(project_id, path)
        return send_from_directory(PROJECTS_DIRECTORY, project_path)
    except Exception as ex:
        if(request.args.get('redirect') == 'false'):
            return send_from_directory(PROJECTS_DIRECTORY, project_path)
        return redirect(url_for('get_project', project_id=project_id, _external=True))


def is_existent_project(project_id):
    if not project_id.strip():
        return False
    return os.path.isdir(get_project_path(project_id))

def get_project_path(project_id):
    return '{}/{}'.format(PROJECTS_DIRECTORY, project_id)

def resolve_project(project_id_param):
    project_id = 'default'
    if project_id_param is not None:
        project_id = project_id_param
    return project_id

def check_process(process_file, project_id):
    tmp = os.popen('ps -Af | grep -w {}'.format(project_id)).read()
    proccount = tmp.count(process_file)

    if proccount > 0:
        raise Exception("Processing files for project_id '{}'. Try later!".format(project_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ['PORT_API'])
