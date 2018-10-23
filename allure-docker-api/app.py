from flask import Flask
from flask import jsonify
from subprocess import call
import os
app = Flask(__name__)

@app.route("/generate-report")
def generate_report():
    process='/app/generateAllureReport.sh'
    try:
        tmp = os.popen('ps -Af').read()
        proccount = tmp.count(process)

        if proccount > 0:
            raise Exception("'Generating Report' process is running currently. Try later!")

        results_directory='/app/allure-results'
        files = os.listdir(results_directory)
        call([process])
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
                'message' : "Report generated successfully"
            }
        }
        resp = jsonify(body)
        resp.status_code = 200

    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)