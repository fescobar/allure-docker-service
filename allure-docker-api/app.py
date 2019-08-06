from flask import Flask, jsonify, render_template, send_file
from flask_swagger_ui import get_swaggerui_blueprint
from subprocess import call
import os, uuid, glob, json
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

GENERATE_REPORT_PROCESS = os.environ['ROOT'] + '/generateAllureReport.sh'
KEEP_HISTORY_PROCESS = os.environ['ROOT'] + '/keepAllureHistory.sh'
CLEAN_HISTORY_PROCESS = os.environ['ROOT'] + '/cleanAllureHistory.sh'
RENDER_EMAIL_REPORT_PROCESS = os.environ['ROOT'] + '/renderEmailableReport.sh'
RESULTS_DIRECTORY = os.environ['RESULTS_DIRECTORY']
ALLURE_VERSION = os.environ['ALLURE_VERSION']
TEST_CASES_DIRECTORY = os.environ['REPORT_DIRECTORY'] + '/data/test-cases/*.json'
EMAILABLE_REPORT_HTML = os.environ['EMAILABLE_REPORT_HTML']
DEFAULT_TEMPLATE = 'default.html'
CSS = "https://stackpath.bootstrapcdn.com/bootswatch/4.3.1/cosmo/bootstrap.css"
SERVER_URL = "http://localhost:" + os.environ['PORT']

if "EMAILABLE_REPORT_CSS_CDN" in os.environ:
    app.logger.info('Overriding CSS')
    CSS = os.environ['EMAILABLE_REPORT_CSS_CDN']

if "SERVER_URL" in os.environ:
    app.logger.info('Overriding Allure Server Url')
    SERVER_URL = os.environ['SERVER_URL']

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

@app.route("/version")
def version():
    try:
        f = open(ALLURE_VERSION, "r")
        version = f.read()
    except Exception, ex:
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

    return resp


@app.route("/generate-report")
def generate_report():
    try:
        check_process(GENERATE_REPORT_PROCESS)

        files = os.listdir(RESULTS_DIRECTORY)

        call([KEEP_HISTORY_PROCESS])
        call([GENERATE_REPORT_PROCESS])
        call([RENDER_EMAIL_REPORT_PROCESS])
    except Exception, ex:
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
                'allure_results_files': files
            },
            'meta_data': {
                'message' : "Report successfully generated"
            }
        }
        resp = jsonify(body)
        resp.status_code = 200

    return resp

@app.route("/clean-history")
def clean_history():
    try:
        check_process(CLEAN_HISTORY_PROCESS)

        call([CLEAN_HISTORY_PROCESS])
    except Exception, ex:
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
                'message' : "History successfully cleaned"
            }
        }
        resp = jsonify(body)
        resp.status_code = 200

    return resp

@app.route("/emailable-report/render")
def emailable_report_render():
    try:
        check_process(GENERATE_REPORT_PROCESS)

        files = glob.glob(TEST_CASES_DIRECTORY)
        testCases = []
        for fileName in files:
            with open(fileName) as f:
                jsonString = f.read().decode("ascii", "ignore")
                app.logger.debug("----TestCase-JSON----")
                app.logger.debug(jsonString)
                testCase = json.loads(jsonString)
                if testCase["hidden"] is False:
                    testCases.append(testCase)

        report = render_template(DEFAULT_TEMPLATE, css=CSS, serverUrl=SERVER_URL, testCases=testCases)

        f = open(EMAILABLE_REPORT_HTML, "w")
        f.write(report)
        f.close()
    except Exception, ex:
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

@app.route("/emailable-report/export")
def emailable_report_export():
    try:
        check_process(GENERATE_REPORT_PROCESS)

        report = send_file(EMAILABLE_REPORT_HTML, as_attachment=True)
    except Exception, ex:
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

def check_process(process_file):
    tmp = os.popen('ps -Af').read()
    proccount = tmp.count(process_file)

    if proccount > 0:
        raise Exception("Processing files. Try later!")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ['PORT_API'])