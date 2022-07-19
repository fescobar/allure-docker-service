"""Sending results to allure server with authentication
"""
import logging
import os
import json
import base64

# pip install requests==2.28.0
from requests import Response, Session

# This directory is where you have all your results locally, generally named as `allure-results`
ALLURE_RESULTS_DIRECTORY = '/allure-results-example'

# This url is where the Allure container is deployed. We are using localhost as example
ALLURE_SERVER_URL = 'http://localhost:5050'

# Project ID according to existent projects in your Allure container
# Check endpoint for project creation >> `[POST]/projects`
PROJECT_ID = 'default'

SECURITY_USER = 'my_username'
SECURITY_PASSWORD = 'my_password'

SEND_RESULTS_URI = f'{ALLURE_SERVER_URL}/allure-docker-service/send-results'
GENERATE_REPORT_URI = f'{ALLURE_SERVER_URL}/allure-docker-service/generate-report'
LOGIN_URI = f'{ALLURE_SERVER_URL}/allure-docker-service/login'
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


def get_authenticated_session() -> Session:
    """Genereting an authenticated http session

    :return: The session object which is used to perform HTTP requests
    :rtype: Session
    """
    logger.info("------------------LOGIN-----------------")
    http_session = Session()
    credentials_body = {
        "username": SECURITY_USER,
        "password": SECURITY_PASSWORD
    }
    response = http_session.post(LOGIN_URI, json=credentials_body, verify=SSL_VERIFICATION)
    log_response(response)

    csrf_access_token = http_session.cookies['csrf_access_token']
    logger.info("CSRF-ACCESS-TOKEN: %s", csrf_access_token)
    http_session.headers['X-CSRF-TOKEN'] = csrf_access_token
    return http_session


def send_results_to_allure_server(http_session: Session):
    """Sending results to allure server with an authenticated session

    :param http_session: The session object which is used to perform HTTP requests
    :type http_session: Session
    """
    logger.info("------------------SEND-RESULTS------------------")

    response = http_session.post(
        SEND_RESULTS_URI,
        params={'project_id': PROJECT_ID},
        json={"results": gather_result_files()},
        verify=SSL_VERIFICATION
    )

    log_response(response)


def generate_allure_report(http_session: Session):
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
    response = http_session.get(GENERATE_REPORT_URI, params=uri_params, verify=SSL_VERIFICATION)
    log_response(response, with_report_url=True)



if __name__ == '__main__':
    session = get_authenticated_session()
    send_results_to_allure_server(session)
    generate_allure_report(session)
