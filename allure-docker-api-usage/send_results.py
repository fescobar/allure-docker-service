import os, requests, json, base64
from requests import Response

# This directory is where you have all your results locally, generally named as `allure-results`
allure_results_directory = '/allure-results-example'
# This url is where the Allure container is deployed. We are using localhost as example
allure_server = 'http://localhost:5050'
# Project ID according to existent projects in your Allure container - Check endpoint for project creation >> `[POST]/projects`
project_id = 'default'
# project_id = 'my-project-id'

# Connection configuration
send_results_uri = f'{allure_server}/allure-docker-service/send-results'
generate_report_uri = f'{allure_server}/allure-docker-service/generate-report'
ssl_verification = True

current_directory = os.path.dirname(os.path.realpath(__file__))
results_directory = current_directory + allure_results_directory
print('RESULTS DIRECTORY PATH: ' + results_directory)


def get_file_as_result(filename):
    file_path = results_directory + "/" + filename
    result = {}

    if os.path.isfile(file_path):
        with open(file_path, "rb") as f:
            content = f.read()
            if content.strip():
                b64_content = base64.b64encode(content)
                result['file_name'] = filename
                result['content_base64'] = b64_content.decode('UTF-8')
                print(f'Successfully encoded result for {file_path}')
                return result
            else:
                print('Empty File skipped: ' + file_path)
    else:
        print('Directory skipped: ' + file_path)


def gather_result_files():
    files = os.listdir(results_directory)
    print('FILES:')
    results = list(filter(lambda f: f is not None, [get_file_as_result(file) for file in files]))
    return results


def log_response(response: Response, with_report_url=False):
    print("STATUS CODE:")
    print(response.status_code)
    print("RESPONSE:")
    json_prettier_response_body = json.dumps(response.json(), indent=4, sort_keys=True)
    print(json_prettier_response_body)
    if with_report_url:
        print('ALLURE REPORT URL:')
        print(response.json()['data']['report_url'])


def send_results_to_allure_server():
    print("------------------SEND-RESULTS------------------")
    request_body = {
        "results": gather_result_files()
    }
    uri_params = {
        'project_id': project_id
    }
    response = requests.post(send_results_uri, params=uri_params, json=request_body, verify=ssl_verification)
    log_response(response)


def generate_allure_report():
    """
    If you want to generate reports on demand use the endpoint `GET /generate-report` and disable the Automatic Execution >> `CHECK_RESULTS_EVERY_SECONDS: NONE`
    """
    print("------------------GENERATE-REPORT------------------")
    execution_name = 'execution from my script'
    execution_from = 'http://google.com'
    execution_type = 'teamcity'

    uri_params = {
        'project_id': project_id, 'execution_name': execution_name, 'execution_from': execution_from,
        'execution_type': execution_type
    }
    response = requests.get(generate_report_uri, params=uri_params, verify=ssl_verification)
    log_response(response, with_report_url=True)


def main():
    send_results_to_allure_server()
    generate_allure_report()


if __name__ == '__main__':
    main()
