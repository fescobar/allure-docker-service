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

Object send_results_to_allure_docker_service(allure_server_url, resultsJson) {
    httpRequest url: "${allure_server_url}/send-results",
                httpMode: 'POST',
                contentType: 'APPLICATION_JSON',
                requestBody: resultsJson,
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
                    def resultsJson = build_allure_results_json(pattern_allure_results_directory)
                    send_results_to_allure_docker_service(allure_server_url, resultsJson)
                }
            }
        }
    }
}
