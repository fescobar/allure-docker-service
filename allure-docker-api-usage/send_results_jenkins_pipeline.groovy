// Required Jenkins plugins:
// https://plugins.jenkins.io/http_request/
// https://plugins.jenkins.io/pipeline-utility-steps/

// Documentation:
// https://jenkins.io/doc/pipeline/steps/pipeline-utility-steps/
// https://jenkins.io/doc/pipeline/steps/workflow-basic-steps/

import groovy.json.JsonOutput;

class Result { String file_name; String content_base64 }

// This url is where the Allure container is deployed. We are using localhost as example
allure_server_url = 'http://localhost:5050'
// Project ID according to existent projects in your Allure container - Check endpoint for project creation >> `[POST]/projects`
project_id = 'default'
//project_id = 'my-project-id'

// This directory is where you have all your results, generally named as `allure-results`
// For the example we are using the results located in 'allure-docker-service/allure-docker-api-usage/allure-results-example'
// Finish the pattern just with 1 asterisk. On this way you avoid to include recursive directories and only you are including files from the first directory level.
pattern_allure_results_directory = '**/**/allure-results-example/*'

automation_repository = 'https://github.com/fescobar/allure-docker-service.git'
default_branch = 'master'

String build_allure_results_json(pattern) {
    def results = []
    def files = findFiles(glob: pattern)
    files.each {
        def b64_content = readFile file: "${it.path}", encoding: 'Base64'
        if (!b64_content.trim().isEmpty()) {
            results.add(new Result(file_name: "${it.name}", content_base64: b64_content))
        } else {
            print("Empty File skipped: ${it.path}")
        }
    }
    JsonOutput.toJson(results: results)
}

Object send_results_to_allure_docker_service(allure_server_url, project_id, results_json) {
    httpRequest url: "${allure_server_url}/allure-docker-service/send-results?project_id=${project_id}",
                httpMode: 'POST',
                contentType: 'APPLICATION_JSON',
                requestBody: results_json,
                consoleLogResponseBody: true,
                validResponseCodes: '200'
}

Object generate_allure_report(allure_server_url, project_id, execution_name, execution_from, execution_type) {
    execution_name = URLEncoder.encode(execution_name, 'UTF-8')
    execution_from = URLEncoder.encode(execution_from, 'UTF-8')
    execution_type = URLEncoder.encode(execution_type, 'UTF-8')

    httpRequest url: "${allure_server_url}/allure-docker-service/generate-report?project_id=${project_id}&execution_name=${execution_name}&execution_from=${execution_from}&execution_type=${execution_type}",
                httpMode: 'GET',
                contentType: 'APPLICATION_JSON',
                consoleLogResponseBody: true,
                validResponseCodes: '200'
}

pipeline {
    agent any
    options {
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Clone Project Testing Repository') {
            steps {
                cleanWs()
                git(url: automation_repository, branch: default_branch)
            }
        }

        stage('Run Tests') {
            steps {
                warnError('Unstable Tests') {
                    print('This stage should be use it to run tests generating allure-results directory')
                }
            }
        }

        stage('Post Results to Allure Docker Service Server') {
            steps {
                script {                    
                    def results_json = build_allure_results_json(pattern_allure_results_directory)
                    send_results_to_allure_docker_service(allure_server_url, project_id, results_json)
                }
            }
        }
/*
        stage('Generate Report in Allure Docker Service Server') {
            steps {
                script {
                    // If you want to generate reports on demand use the endpoint `GET /generate-report` and disable the Automatic Execution >> `CHECK_RESULTS_EVERY_SECONDS: NONE`
                    def execution_name = 'execution from my jenkins'
                    def execution_from = "$BUILD_URL"
                    def execution_type = 'jenkins'
                    def response = generate_allure_report(allure_server_url, project_id, execution_name, execution_from, execution_type)
                    def response_body = readJSON text: response.content
                    print "ALLURE REPORT URL: $response_body.data.report_url"
                }
            }
        }
*/
    }
}
