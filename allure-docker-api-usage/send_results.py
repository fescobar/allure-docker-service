import os, requests, json, base64, argparse, zipfile

def parse_args():
    parser = argparse.ArgumentParser(description='Upload the test results to the Allure Docker Service')
    optional = parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    required.add_argument('-r', '--results-dir', required=True, help='Directory path to where the results are stored locally')
    required.add_argument('-a', '--allure-server', required=True, help='URL pointing to the Allure Service e.g. http://localhost:5050')
    optional.add_argument('-p', '--project', default='default', metavar='', help='The project ID to upload the results for')
    optional.add_argument('-f', '--force', action='store_true', help='Set if you want to force the creation of the project')
    optional.add_argument('-j', '--json', action='store_true', help='Set if you want to send all of the results as json data')
    optional.add_argument('-s', '--secure', action='store_true', help='Set if the Allure Docker Service is configure with access credentials')
    optional.add_argument('--username', metavar='', help='Username for the Allure Service')
    optional.add_argument('--password', metavar='', help='Password for the Allure Service')
    optional.add_argument('--no-ssl', dest='ssl' , action='store_false', help='Set if you do not want to verify SSL')
    optional.add_argument('-c', '--compress', action='store_true', help='Set if you want to compress the results before sending')
    optional.add_argument('-g', '--generate', action='store_true', help='Set if you want to generate the report after uploading the results')
    optional.add_argument('--exec-name', metavar='', help="Name of the test execution")
    optional.add_argument('--exec-from', metavar='', help="URL pointing to the execution")
    optional.add_argument('--exec-type', metavar='', help="Execution type e.g. Jenkins, GitLab etc")
    parser._action_groups.append(optional)

    args = parser.parse_args()

    if args.secure and (args.username is None or args.password is None):
        parser.error('-s, --secure requires --username and --password')

    if args.json and args.compress:
        parser.error('-j, --json and -c,--compress cannot be used together')

    if (args.exec_name is not None or args.exec_from is not None or args.exec_type is not None) and not args.generate:
        parser.error('--exec-name, --exec-from and --exec-type cannot be used if -g,--generate is not set')

    return args
    
def login_allure(args):
    print("------------------LOGIN-----------------")
    credentials_body = {
        "username": args.username,
        "password": args.password
    }

    session = requests.Session()
    response = session.post(args.allure_server + '/allure-docker-service/login', json=credentials_body, verify=args.ssl)

    print("STATUS CODE:")
    print(response.status_code)
    print("RESPONSE COOKIES:")
    json_prettier_response_body = json.dumps(session.cookies.get_dict(), indent=4, sort_keys=True)
    print(json_prettier_response_body)
    csrf_access_token = session.cookies['csrf_access_token']
    print("CSRF-ACCESS-TOKEN: " + csrf_access_token)
    session.headers.update({"X-CSRF-TOKEN": csrf_access_token})

    return session

def send_results(args, session, request_args):
    print("------------------SEND-RESULTS------------------")
    if session is not None:
        response = session.post(args.allure_server + '/allure-docker-service/send-results?project_id={}&force_project_creation={}'.format(args.project, str(args.force).lower()), **request_args)
    else:
        response = requests.post(args.allure_server + '/allure-docker-service/send-results?project_id={}&force_project_creation={}'.format(args.project, str(args.force).lower()), **request_args)

    print("STATUS CODE:")
    print(response.status_code)
    print("RESPONSE:")
    json_response_body = json.loads(response.content)
    json_prettier_response_body = json.dumps(json_response_body, indent=4, sort_keys=True)
    print(json_prettier_response_body)

def generate_report(args, session):
    print("------------------GENERATE-REPORT------------------")
    url = '{}/allure-docker-service/generate-report?project_id={}'.format(args.allure_server, args.project)

    if args.exec_name is not None:
        url += '&execution_name={}'.format(args.exec_name)
    if args.exec_from is not None:
        url += '&execution_from={}'.format(args.exec_from)
    if args.exec_type is not None:
        url += '&execution_type={}'.format(args.exec_type)

    if session is not None:
        response = session.get(url, verify=args.ssl)
    else:
        response = requests.get(url, verify=args.ssl)

    print("STATUS CODE:")
    print(response.status_code)
    print("RESPONSE:")
    json_response_body = json.loads(response.content)
    json_prettier_response_body = json.dumps(json_response_body, indent=4, sort_keys=True)
    print(json_prettier_response_body)

    print('ALLURE REPORT URL:')
    print(json_response_body['data']['report_url'])

def get_json_results(results_dir):
    results = []
    print('FILES:')
    for root, dirs, files in os.walk(results_dir):    
        for file in files:
            result = {}
            filepath = os.path.join(root, file)
            print(filepath)
            with open(filepath, "rb") as f:
                content = f.read()
                if content.strip():
                    b64_content = base64.b64encode(content)
                    result['file_name'] = file
                    result['content_base64'] = b64_content.decode('UTF-8')
                    results.append(result)
                else:
                    print('Empty File skipped: '+ filepath)
    return {'results': results}

def get_results_files_compressed(results_dir):
    with zipfile.ZipFile('/tmp/results.zip', mode='w') as archive:
        for root, dirs, files in os.walk(results_dir):
            for file in files:
                archive.write(os.path.join(root, file), file)

    return {'files[]': ('results.zip', open('/tmp/results.zip', 'rb'))}

def get_results_files():
    files = []
    for root, dirs, files in os.walk(args.results_dir):
        for file in files:
            filepath = os.path.join(root, file)
            files.append(('files[]', open(filepath, 'rb')))

    return files

args = parse_args()

print('RESULTS DIRECTORY PATH: ' + args.results_dir)

request_args = {}

if args.json:
    request_args['json'] = get_json_results(args.results_dir)
elif args.compress:
    request_args['files'] = get_results_files_compressed(args.results_dir)
else:
    request_args['files'] = get_results_files(args.results_dir)

session = None
if args.secure:
    session = login_allure(args)

send_results(args, session, request_args)

if args.generate:
    generate_report(args, session)
