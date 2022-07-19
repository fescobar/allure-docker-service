"""Sending results to allure server without authentication
"""
import logging
import os
import json
import base64

# pip install requests==2.28.0
from requests import Response, post, get


# This directory is where you have all your results locally, generally named as `allure-results`
ALLURE_RESULTS_DIRECTORY = '/allure-results-example'

# This url is where the Allure container is deployed. We are using localhost as example
ALLURE_SERVER_URL = 'http://localhost:5050'

# Project ID according to existent projects in your Allure container
# Check endpoint for project creation >> `[POST]/projects`
PROJECT_ID = 'default'

SEND_RESULTS_URI = f'{ALLURE_SERVER_URL}/allure-docker-service/send-results'
GENERATE_REPORT_URI = f'{ALLURE_SERVER_URL}/allure-docker-service/generate-report'
SSL_VERIFICATION = True

current_directory = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(__name__)
results_directory = current_directory + ALLURE_RESULTS_DIRECTORY
logger.info('RESULTS DIRECTORY PATH: %s', results_directory)


def get_file_as_result(filename: str) -> dict[str, str] | None:
    """

    :param filename: the file path
    :type filename: str
    :return: Either a dictionnary of the file path and the content encoded in base64, or nothing
    :rtype: dict[str, str] | None
    """
    file_path = results_directory + "/" + filename

    if os.path.isfile(file_path):
        with open(file_path, "rb") as file:
            content = file.read()
            if content.strip():
                b64_content: bytes = base64.b64encode(content)
                result = {
                    'file_name': filename,
                    'content_base64': b64_content.decode('UTF-8')
                }
                logger.info('Successfully encoded result for %s', file_path)
                return result
            else:
                logger.info('Empty File skipped: %s', file_path)
    else:
        logger.info('Directory skipped: %s', file_path)


def gather_result_files() -> list[dict[str, str]]:
    """Gather results files and returns a list of file paths
    """
    files: list[str] = os.listdir(results_directory)
    logger.info('FILES:')
    return [get_file_as_result(file) for file in files if get_file_as_result(file)]


def log_response(response: Response, with_report_url: bool = False) -> None:
    """Displays the status code and the body of the response
    """
    logger.info("STATUS CODE: %i", response.status_code)
    logger.info("RESPONSE:")
    json_prettier_response_body = json.dumps(response.json(), indent=4, sort_keys=True)
    logger.info(json_prettier_response_body)
    if with_report_url:
        logger.info('ALLURE REPORT URL:')
        logger.info(response.json()['data']['report_url'])


def send_results_to_allure_server() -> None:
    """Sending results to allure server
    """
    logger.info("------------------SEND-RESULTS------------------")
    request_body = {
        "results": gather_result_files()
    }
    uri_params = {
        'project_id': PROJECT_ID
    }
    response = post(SEND_RESULTS_URI, params=uri_params, json=request_body, verify=SSL_VERIFICATION)
    log_response(response)


def generate_allure_report() -> None:
    """
    If you want to generate reports on demand use the endpoint `GET /generate-report`
    and disable the Automatic Execution >> `CHECK_RESULTS_EVERY_SECONDS: NONE`
    """
    logger.info("------------------GENERATE-REPORT------------------")
    execution_name = 'execution from my script'
    execution_from = 'http://google.com'
    execution_type = 'teamcity'

    uri_params = {
        'project_id': PROJECT_ID,
        'execution_name': execution_name,
        'execution_from': execution_from,
        'execution_type': execution_type
    }
    response = get(GENERATE_REPORT_URI, params=uri_params, verify=SSL_VERIFICATION)
    log_response(response, with_report_url=True)


if __name__ == '__main__':
    send_results_to_allure_server()
    generate_allure_report()
