import os
import re
import json
import subprocess

storage = None

def setup_storage(storage_instance):
    global storage
    storage = storage_instance

def keep_allure_history(project_id):
    static_content_projects = os.getenv('STATIC_CONTENT_PROJECTS')
    keep_history = os.getenv('KEEP_HISTORY', 'false').lower()  # Default to 'false' if not set
    project_reports_directory = os.path.join(static_content_projects, project_id, 'reports')
    project_results_history = os.path.join(static_content_projects, project_id, 'results', 'history')
    project_latest_report = os.path.join(project_reports_directory, 'latest', 'history')

    # Create history in results directory
    if keep_history in ["TRUE", "true", "1"]:
        print(f"Creating history on results directory for project_id: {project_id} ...")
        storage.mkdir(project_results_history)
        if storage.exists(project_latest_report):
            print("Copying history from previous results...")
            storage.copy_dir(project_latest_report, project_results_history)
    else:
        # Remove the history directory if it exists
        if storage.isdir(project_results_history):
            print(f"Removing history directory from results for project_id: {project_id} ...")
            storage.rmdir(project_results_history)

def generate_allure_report(EXEC_STORE_RESULTS_PROCESS, project_id, origin='api', execution_name='Automatic Execution', execution_from='', execution_type='another'):
    STATIC_CONTENT_PROJECTS = os.getenv('STATIC_CONTENT_PROJECTS')
    EMAILABLE_REPORT_FILE_NAME = os.getenv('EMAILABLE_REPORT_FILE_NAME')
    EXECUTOR_FILENAME = os.getenv('EXECUTOR_FILENAME')
    OPTIMIZE_STORAGE = os.getenv('OPTIMIZE_STORAGE')
    KEEP_HISTORY = os.getenv('KEEP_HISTORY')
    ALLURE_RESOURCES = os.getenv('ALLURE_RESOURCES')
    ROOT = os.getenv('ROOT')
    PROJECT_REPORTS = os.path.join(STATIC_CONTENT_PROJECTS, project_id, 'reports')
    STORAGE_TYPE = os.getenv('STORAGE_TYPE', 'local')

    # Get the last report directory, similar logic to Bash script
    last_report_path_directory = None
    if storage.listdir(PROJECT_REPORTS):
        directories = [d for d in storage.listdir(PROJECT_REPORTS) if storage.isdir(os.path.join(PROJECT_REPORTS, d))]
        if 'latest' in directories:
            directories.remove('latest')
        directories = sorted(
            directories, reverse=True,
            key=lambda x: storage.getmtime(os.path.join(PROJECT_REPORTS, x, 'dummyfile')) if STORAGE_TYPE == 's3' else storage.getmtime(os.path.join(PROJECT_REPORTS, x))
        )
        if directories:
            last_report_path_directory = os.path.join(PROJECT_REPORTS, directories[0])

    LAST_REPORT_DIRECTORY = os.path.basename(last_report_path_directory) if last_report_path_directory else None


    if STORAGE_TYPE == 's3':
        TEMP_PROJECT_DIRECTORY = os.path.join("/tmp/allure-results", project_id)
        RESULTS_DIRECTORY = os.path.join(TEMP_PROJECT_DIRECTORY, 'results')
        PROJECT_REPORTS = os.path.join(TEMP_PROJECT_DIRECTORY, 'reports')
    else:
        RESULTS_DIRECTORY = os.path.join(STATIC_CONTENT_PROJECTS, project_id, 'results')
    if not os.path.exists(RESULTS_DIRECTORY):
        os.makedirs(RESULTS_DIRECTORY)

    EXECUTOR_PATH = os.path.join(RESULTS_DIRECTORY, EXECUTOR_FILENAME)
    print(f"Creating {EXECUTOR_FILENAME} for project_id: {project_id}")

    if LAST_REPORT_DIRECTORY != "latest":
        build_order = int(LAST_REPORT_DIRECTORY) + 1 if LAST_REPORT_DIRECTORY else 1
        EXECUTOR_JSON = {
            "reportName": project_id,
            "buildName": f"{project_id} #{build_order}",
            "buildOrder": build_order,
            "name": execution_name,
            "reportUrl": f"../{build_order}/index.html",
            "buildUrl": execution_from,
            "type": execution_type
        }
        if EXEC_STORE_RESULTS_PROCESS == "1":
            with open(EXECUTOR_PATH, 'w') as file:
                json.dump(EXECUTOR_JSON, file)
        else:
            with open(EXECUTOR_PATH, 'w') as file:
                file.write('')
    else:
        with open(EXECUTOR_PATH, 'w') as file:
            file.write('')

    if STORAGE_TYPE == 's3':
        storage.get_files(os.path.join(STATIC_CONTENT_PROJECTS, project_id, 'results'), TEMP_PROJECT_DIRECTORY)
    
    subprocess.run(['allure', 'generate', '--clean', RESULTS_DIRECTORY, '-o', os.path.join(PROJECT_REPORTS, 'latest')])
    
    if OPTIMIZE_STORAGE == "1":
        create_or_update_symlink(ALLURE_RESOURCES + '/app.js', os.path.join(PROJECT_REPORTS, 'latest', 'app.js'))
        create_or_update_symlink(ALLURE_RESOURCES + '/styles.css', os.path.join(PROJECT_REPORTS, 'latest', 'styles.css'))

    if STORAGE_TYPE == 's3':
        storage.put_files(os.path.join(PROJECT_REPORTS, 'latest'), os.path.join(STATIC_CONTENT_PROJECTS, project_id, 'reports', 'latest'))
    
    if KEEP_HISTORY in ["TRUE", "true", "1"]:
        if EXEC_STORE_RESULTS_PROCESS == "1":
            store_allure_report(project_id, str(build_order))

    keep_allure_latest_history(project_id)


def store_allure_report(project_id, build_order):
    static_content_projects = os.environ.get('STATIC_CONTENT_PROJECTS')
    project_reports_directory = os.path.join(static_content_projects, project_id, 'reports')
    project_latest_report = os.path.join(project_reports_directory, 'latest')

    # Check if the latest report directory is not empty
    if storage.listdir(project_latest_report):
        print(f"Storing report history for PROJECT_ID: {project_id}")
        new_report_directory = os.path.join(project_reports_directory, build_order)
        storage.mkdir(new_report_directory)
        storage.copy_dir(project_latest_report, new_report_directory)

def keep_allure_latest_history(project_id):
    keep_history = os.environ.get('KEEP_HISTORY')
    keep_history_latest = os.environ.get('KEEP_HISTORY_LATEST')
    static_content_projects = os.environ.get('STATIC_CONTENT_PROJECTS')
    email_report_file_name = os.environ.get('EMAILABLE_REPORT_FILE_NAME')
    
    if keep_history.lower() == 'true' or keep_history == '1':
        project_reports_directory = os.path.join(static_content_projects, project_id, 'reports')
        keep_latest = 20
        if re.match('^[0-9]+$', keep_history_latest):
            keep_latest = int(keep_history_latest)

        report_files = [f for f in storage.listdir(project_reports_directory) if f != 'latest' and f != '0' and email_report_file_name not in f]
        
        current_size = len(report_files)

        if current_size > keep_latest:
            size_to_remove = current_size - keep_latest
            print(f"Keeping latest {keep_latest} history reports for PROJECT_ID: {project_id}")
            
            files_to_remove = sorted(report_files)[:size_to_remove]
            
            for file in files_to_remove:
                storage.rmdir(os.path.join(project_reports_directory, file))
                print(f"Removed: {file}")


def clean_allure_results(project_id):
    print(f"Cleaning results for PROJECT_ID: {project_id}")
    project_results_directory = os.path.join(os.environ['STATIC_CONTENT_PROJECTS'], str(project_id), 'results')

    # Check if the directory is not empty
    files = storage.listdir(project_results_directory)
    if files:
        # Loop through files in the directory and remove each file
        for filename in files:
            file_path = os.path.join(project_results_directory, filename)
            if storage.isfile(file_path):  # Ensuring it's a file and not a directory
                storage.remove(file_path)
    
    print(f"Results cleaned for PROJECT_ID: {project_id}")


def create_or_update_symlink(source, target):
    if os.path.exists(target) or os.path.islink(target):
        os.remove(target)
    os.symlink(source, target)