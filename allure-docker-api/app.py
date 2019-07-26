from flask import Flask
from flask import jsonify
from subprocess import call
import os
app = Flask(__name__)

@app.route("/version")
def version():
    try:
        f = open("/app/version", "r")
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
    historyProcess='/app/keepAllureHistory.sh'
    generateReportProcess='/app/generateAllureReport.sh'
    try:
        tmp = os.popen('ps -Af').read()
        proccount = tmp.count(generateReportProcess)

        if proccount > 0:
            raise Exception("'Generating Report' process is running currently. Try later!")

        results_directory='/app/allure-results'
        files = os.listdir(results_directory)

        call([historyProcess])
        call([generateReportProcess])
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
    cleanHistoryProcess='/app/cleanAllureHistory.sh'
    try:
        tmp = os.popen('ps -Af').read()
        proccount = tmp.count(cleanHistoryProcess)

        if proccount > 0:
            raise Exception("'Clean History' process is running currently. Try later!")

        call([cleanHistoryProcess])
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ['PORT_API'])