[![](resources/allure.png)](http://allure.qatools.ru/)
[![](resources/docker.png)](https://docs.docker.com/)

# ALLURE DOCKER SERVICE
Table of contents
=================
   * [FEATURES](#FEATURES)
      * [Docker Hub](#docker-hub)
      * [Docker Versions](#docker-versions)
   * [USAGE](#USAGE)
      * [Generate Allure Results](#generate-allure-results)
      * [ALLURE DOCKER SERVICE](#allure-docker-service-1)
          * [SINGLE PROJECT - LOCAL REPORTS](#SINGLE-PROJECT---LOCAL-REPORTS)
            * [Single Project - Docker on Unix/Mac](#single-project---docker-on-unixmac)
            * [Single Project - Docker on Windows (Git Bash)](#single-project---docker-on-windows-git-bash)
            * [Single Project - Docker Compose](#single-project---docker-compose)
          * [MULTIPLE PROJECTS - REMOTE REPORTS](#MULTIPLE-PROJECTS---REMOTE-REPORTS)
            * [Multiple Project - Docker on Unix/Mac](#multiple-project---docker-on-unixmac)
            * [Multiple Project - Docker on Windows (Git Bash)](#multiple-project---docker-on-windows-git-bash)
            * [Multiple Project - Docker Compose](#multiple-project---docker-compose)
            * [Creating our first project](#creating-our-first-project)
      * [PORT 4040 Deprecated](#port-4040-deprecated)
      * [Known Issues](#known-issues)
      * [Opening & Refreshing Report](#opening--refreshing-report)
      * [New User Interface](#new-user-interface)
      * [Deploy using Kubernetes](#deploy-using-kubernetes)
      * [Extra options](#extra-options)
          * [Allure API](#allure-api)
            * [Info Endpoints](#info-endpoints)
            * [Action Endpoints](#action-endpoints)
            * [Project Endpoints](#project-endpoints)
          * [Send results through API](#send-results-through-api)
            * [Content-Type - application/json](#content-type---applicationjson)
            * [Content-Type - multipart/form-data](#content-type---multipartform-data)
            * [Force Project Creation Option](#force-project-creation-option)
          * [Customize Executors Configuration](#customize-executors-configuration)
          * [API Response Less Verbose](#api-response-less-verbose)
          * [Switching version](#switching-version)
          * [Switching port](#switching-port)
          * [Updating seconds to check Allure Results](#updating-seconds-to-check-allure-results)
          * [Keep History and Trends](#keep-history-and-trends)
          * [Override User Container](#override-user-container)
          * [Start in DEV Mode](#start-in-dev-mode)
          * [Enable TLS](#enable-tls)
          * [Enable Security](#enable-security)
            * [Login](#login)
            * [X-CSRF-TOKEN](#x-csrf-token)
            * [Refresh Access Token](#refresh-access-token)
            * [Logout](#logout)
            * [Roles](#roles)
            * [Make Viewer endpoints public](#make-viewer-endpoints-public)
            * [Scripts](#scripts)
          * [Add Custom URL Prefix](#add-custom-url-prefix)
          * [Optimize Storage](#optimize-storage)
          * [Export Native Full Report](#export-native-full-report)
          * [Customize Emailable Report](#customize-emailable-report)
              * [Override CSS](#override-css)
              * [Override title](#override-title)
              * [Override server link](#override-server-link)
              * [Develop a new template](#develop-a-new-template)
          * [Allure Customized Plugins](#allure-customized-plugins)
          * [Allure Options](#allure-options)
   * [SUPPORT](#SUPPORT)
      * [Gitter](#gitter)
   * [DOCKER GENERATION (Usage for developers)](#docker-generation-usage-for-developers)

## FEATURES
Allure Framework provides you good looking reports for automation testing.
For using this tool is required to install a server. You could have this server running on Jenkins or if you want to see reports locally, you need to run some commands on your machine. This work results tedious, at least for me :)

For that reason, this docker container allows you to see up to date reports simply mounting your `allure-results` directory (for a Single Project) or your `projects` directory (for Multiple Projects). Every time appears new results (generated for your tests), Allure Docker Service will detect those changes and it will generate a new report automatically (optional: send results / generate report through API), what you will see refreshing your browser.

- Useful for developers who wants to run tests locally and want to see what were the problems during regressions.
- Useful for the team to check the tests status for every project.

### Docker Hub
- Repository: [frankescobar/allure-docker-service](https://hub.docker.com/r/frankescobar/allure-docker-service/)

### Docker Versions
Docker container versions are based on binary [Allure 2 releases](https://github.com/allure-framework/allure2/releases/)

#### Image Variants
Allure Docker Service supports architectures amd64, arm32v7 and arm64v8.

- Tags: https://hub.docker.com/r/frankescobar/allure-docker-service/tags

The following table shows the variation of provided images.

|**Tag**         |**Base Image**                              |**Arch** | **OS** |
|----------------|--------------------------------------------|---------|--------|
| 0.20.7-amd64   | amd64/adoptopenjdk:11-jre-openj9-bionic    | amd64   | ubuntu |
| 0.20.7-arm32v7 | arm32v7/adoptopenjdk:11-jdk-hotspot-bionic | arm32v7 | ubuntu |
| 0.20.7-arm64v8 | arm64v8/adoptopenjdk:11-jre-hotspot-bionic | arm64v8 | ubuntu |

The following table shows the provided Manifest Lists.

| **Tag**                                | **allure-docker-service Base Image**              |
|----------------------------------------|---------------------------------------------------|
| latest, 2.13.8                         | frankescobar/allure-docker-service:2.13.8-amd64   |
|                                        | frankescobar/allure-docker-service:2.13.8-arm32v7 |
|                                        | frankescobar/allure-docker-service:2.13.8-arm64v8 |

## USAGE
### Generate Allure Results
First at all it's important to be clear. This container only generates reports based on results. You have to generate allure results according to the technology what are you using.

Reference: https://github.com/fescobar/allure-docker-service-examples

We have some examples projects:
- [allure-docker-java-testng-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-java-testng-example)
- [allure-docker-java-junit4-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-java-junit4-example)
- [allure-docker-java-cucumber-jvm-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-java-cucumber-jvm-example)
- [allure-docker-nodejs-cucumber-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-nodejs-cucumber-example)
- [allure-docker-nodejs-typescript-cucumber-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-nodejs-typescript-cucumber-example)
- [allure-docker-nodejs-typescript-mocha-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-nodejs-typescript-mocha-example)
- [allure-docker-python-behave-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-python-behave-example)
- [allure-docker-python-pytest-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-python-pytest-example)
- [AllureDockerCSharpExample](https://github.com/fescobar/allure-docker-service-examples/tree/master/AllureDockerCSharpExample)
- [AllureDockerCSharpSpecFlow3Example](https://github.com/fescobar/allure-docker-service-examples/tree/master/AllureDockerCSharpSpecFlow3Example)

In this case we are going to generate results using the java project [allure-docker-java-testng-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-java-testng-example) of this repository.

Go to directory [allure-docker-java-testng-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-java-testng-example) via command line:

```sh
cd allure-docker-java-testng-example
```
Execute:

```sh
mvn test -Dtest=FirstTest
```
If everything is OK, you should see something like this:

```sh
[INFO] -------------------------------------------------------
[INFO]  T E S T S
[INFO] -------------------------------------------------------
[INFO] Running com.allure.docker.FirstTest
13:19:03.028 [main] INFO com.allure.docker.FirstTest - test1
13:19:03.044 [main] DEBUG io.qameta.allure.AllureLifecycle - Adding attachment to item with uuid 4b282bd9-6a0f-4fc3-a5cc-be6e8220d3c6
13:19:03.124 [main] INFO com.allure.docker.FirstTest - test2
13:19:03.133 [main] DEBUG io.qameta.allure.AllureLifecycle - Adding attachment to item with uuid e2097440-e9e8-46e9-8b9d-09467b5a49b1
[ERROR] Tests run: 2, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 1.702 s <<< FAILURE! - in com.allure.docker.FirstTest
[ERROR] test2(com.allure.docker.FirstTest)  Time elapsed: 0.028 s  <<< FAILURE!
java.lang.AssertionError: FAILURE ON PURPOSE
        at com.allure.docker.FirstTest.test2(FirstTest.java:37)

[INFO]
[INFO] Results:
[INFO]
[ERROR] Failures:
[ERROR]   FirstTest.test2:37 FAILURE ON PURPOSE
[INFO]
[ERROR] Tests run: 2, Failures: 1, Errors: 0, Skipped: 0
[INFO]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  4.600 s
[INFO] Finished at: 2019-09-16T13:19:03+01:00
[INFO] ------------------------------------------------------------------------
```

There are 2 tests, one of them failed. Now you can see the `allure-results` diretory was created inside of [allure-docker-java-testng-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-java-testng-example) project.

Just it has left 1 step more. You have to run `allure-docker-service` mounting your `allure-results` directory.

Start the container for a single project -> [SINGLE PROJECT - LOCAL REPORTS](#SINGLE-PROJECT---LOCAL-REPORTS)

### ALLURE DOCKER SERVICE
Docker Image: https://hub.docker.com/r/frankescobar/allure-docker-service/

|  **Project Type**   |  **Port**  |       **Volume Path**     |  **Container Volume Path**   |
|---------------------|------------|---------------------------|------------------------------|
|  Single Project     |    5050    |   ${PWD}/allure-results   |    /app/allure-results       |
|                     |            |   ${PWD}/allure-reports   |    /app/default-reports      |
|  Multiple Projects  |    5050    |   ${PWD}/projects         |    /app/projects             |

To improve the navigability is recommended to install an Extension/AddOn in your browser:
- Google Chrome >  JSONView > https://chrome.google.com/webstore/detail/jsonview/chklaanhfefbnpoihckbnefhakgolnmc?hl=en
- Mozilla Firefox > JSONView > https://addons.mozilla.org/en-US/firefox/addon/jsonview/

NOTE:
- Check the [New User Interface](#new-user-interface)

#### SINGLE PROJECT - LOCAL REPORTS
This option is recommended for local executions. You should attach the volume where your results are being generated locally for your automation project. 

All the information related local executions will be stored in the `default` project what is created when you start the container. You can see the complete info using the `GET /projects/default` endpoint:

- http://localhost:5050/allure-docker-service/projects/default

##### Single Project - Docker on Unix/Mac
From this directory [allure-docker-java-testng-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-java-testng-example) execute next command:
```sh
      docker run -p 5050:5050 -e CHECK_RESULTS_EVERY_SECONDS=3 -e KEEP_HISTORY=1 \
                 -v ${PWD}/allure-results:/app/allure-results \
                 -v ${PWD}/allure-reports:/app/default-reports \
                 frankescobar/allure-docker-service
```

##### Single Project - Docker on Windows (Git Bash)
From this directory [allure-docker-java-testng-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-java-testng-example) execute next command:
```sh
      docker run -p 5050:5050 -e CHECK_RESULTS_EVERY_SECONDS=3 -e KEEP_HISTORY=1 \
                 -v "/$(pwd)/allure-results:/app/allure-results" \
                 -v "/$(pwd)/allure-reports:/app/default-reports" \
                 frankescobar/allure-docker-service
```

##### Single Project - Docker Compose
Using docker-compose is the best way to manage containers: [allure-docker-java-testng-example/docker-compose.yml](https://github.com/fescobar/allure-docker-service-examples/blob/master/allure-docker-java-testng-example/docker-compose.yml)

```sh
version: '3'
services:
  allure:
    image: "frankescobar/allure-docker-service"
    environment:
      CHECK_RESULTS_EVERY_SECONDS: 1
      KEEP_HISTORY: 1
    ports:
      - "5050:5050"
    volumes:
      - ${PWD}/allure-results:/app/allure-results
      - ${PWD}/allure-reports:/app/default-reports
```

From this directory [allure-docker-java-testng-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-java-testng-example) execute next command:

```sh
docker-compose up allure
```

If you want to run in background:

```sh
docker-compose up -d allure
```

You can see the logs:

```sh
docker-compose logs -f allure
```

NOTE:
- Check the [New User Interface](#new-user-interface)
- Read about [PORT 4040 Deprecated](#port-4040-deprecated) in case you are using previous versions.
- The `${PWD}/allure-results` directory could be in anywhere on your machine. Your project must generate results in that directory.
- The `/app/allure-results` directory is inside of the container. You MUST NOT change this directory, otherwise, the container won't detect the new changes.
- The `/app/default-reports` directory is inside of the container. You MUST NOT change this directory, otherwise, the history reports won't be stored.

NOTE FOR WINDOWS USERS:
- `${PWD}` determines the current directory. This only works for [GIT BASH](https://git-scm.com/downloads). If you want to use PowerShell or CMD you need to put your full path to `allure-results` directory or find the way to get the current directory path using those tools.

#### MULTIPLE PROJECTS - REMOTE REPORTS
`Available from Allure Docker Service version 2.13.3`

With this option you could generate multiple reports for multiple projects, you can create, delete and get projects using [Project Endpoints](#project-endpoints). You can use Swagger documentation to help you.

IMPORTANT NOTE:
- For multiple projects configuration you must use `CHECK_RESULTS_EVERY_SECONDS` with value `NONE`. Otherwise, your performance machine would be affected, it could consume high memory, processors and storage. Use the endpoint `GET /generate-report` on demand after sending the results `POST /send-results`.
- If you use automatic reports a daemom is created and it will be listening any change in the `results` directory it will generate a new report each time find a new file. The same will happen for every project. For that reason, it's convenient disable the automatic reports using the value `NONE` in `CHECK_RESULTS_EVERY_SECONDS`.

##### Multiple Project - Docker on Unix/Mac
```sh
      docker run -p 5050:5050 -e CHECK_RESULTS_EVERY_SECONDS=NONE -e KEEP_HISTORY=1 \
                 -v ${PWD}/projects:/app/projects \
                 frankescobar/allure-docker-service
```

##### Multiple Project - Docker on Windows (Git Bash)
```sh
      docker run -p 5050:5050 -e CHECK_RESULTS_EVERY_SECONDS=NONE -e KEEP_HISTORY=1 \
                 -v "/$(pwd)/projects:/app/projects" \
                 frankescobar/allure-docker-service
```

##### Multiple Project - Docker Compose
Using docker-compose is the best way to manage containers: [allure-docker-multi-project-example/docker-compose.yml](https://github.com/fescobar/allure-docker-service-examples/blob/master/allure-docker-multi-project-example/docker-compose.yml)

```sh
version: '3'
services:
  allure:
    image: "frankescobar/allure-docker-service"
    environment:
      CHECK_RESULTS_EVERY_SECONDS: NONE
      KEEP_HISTORY: 1
      KEEP_HISTORY_LATEST: 25
    ports:
      - "5050:5050"
    volumes:
      - ${PWD}/projects:/app/projects
```

```sh
docker-compose up allure
```

If you want to run in background:

```sh
docker-compose up -d allure
```

You can see the logs:

```sh
docker-compose logs -f allure
```

NOTE:
- Check the [New User Interface](#new-user-interface)
- Check [Deploy using Kubernetes](#deploy-using-kubernetes)
- Read about [PORT 4040 Deprecated](#port-4040-deprecated) in case you are using previous versions.
- The `/app/projects` directory is inside of the container. You MUST NOT change this directory, otherwise, the information about projects won't be stored.

NOTE FOR WINDOWS USERS:
- `${PWD}` determines the current directory. This only works for [GIT BASH](https://git-scm.com/downloads). If you want to use PowerShell or CMD you need to put your full path to `allure-results` directory or find the way to get the current directory path using those tools.


##### Creating our first project

- Creating the project `my-project-id` using the endpoint `POST /projects`:

[![](resources/allure-mp00.png)](resources/allure-mp00.png)


- You can see all the existent projects using the endpoint `GET /projects`:

[![](resources/allure-mp01.png)](resources/allure-mp01.png)

- The `default` project is always created automatically, it shouldn't be removed.

- And get specific information using the endpoint `GET /projects/{id}`

[![](resources/allure-mp02.png)](resources/allure-mp02.png)


If we want to generate reports for this specific project we need to use the same [Action Endpoints](#action-endpoints) that we used for a single project, but the difference now is we need to use the query parameter `project_id` to specify our new project.

For example if we want to get the `latest` report for a `single project`, generally we execute this command:
- http://localhost:5050/allure-docker-service/latest-report    >>      http://localhost:5050/allure-docker-service/projects/default/reports/latest/index.html?redirect=false

This command will return the `latest` report from the `default` project as you see in the url above

If we want to get the `latest` report from our new project we need to execute this one:
- http://localhost:5050/allure-docker-service/latest-report?project_id=my-project-id     >>      http://localhost:5050/allure-docker-service/projects/my-project-id/reports/latest/index.html?redirect=false

You can appreciate the difference in the path `/projects/{PROJECT_ID}/....`

You can use any [Action Endpoints](#action-endpoints), but don't forget to pass the parameter `project_id` with the right project id that you want to interact with it.

'GET'      /latest-report`?project_id=my-project-id`

'POST'     /send-results`?project_id=my-project-id`

'GET'      /generate-report`?project_id=my-project-id`

'GET'      /clean-results`?project_id=my-project-id`

'GET'      /clean-history`?project_id=my-project-id`

'GET'      /emailable-report/render`?project_id=my-project-id`

'GET'      /emailable-report/export`?project_id=my-project-id`

'GET'      /report/export`?project_id=my-project-id`

We are going to attach our volume NOT for our `local allure-results`. For this case is necessary to store the information regarding all our projects. The project structure is this one:
```sh
projects
   |-- default
   |   |-- results
   |   |-- reports
   |   |   |-- latest
   |   |   |-- ..
   |   |   |-- 3
   |   |   |-- 2
   |   |   |-- 1
   |-- my-project-id
   |   |-- results
   |   |-- reports
   |   |   |-- latest
   |   |   |-- ..
   |   |   |-- 3
   |   |   |-- 2
   |   |   |-- 1

```

NOTE:
- You MUST NOT MODIFY MANUALLY the structure directory of any project, you could affect the right behaviour.
- If you don't attach your volume with the proper path `/app/projects` you will lost the information about the projects generated for you.


### PORT 4040 Deprecated
The first versions of this container used port `4040` for Allure Report and port `5050` for Allure API.

The latest version includes new features `Multiple Projects` & `Navigate detailed previous history/trends`. These improvements allow us to handle multiple projects and multiple history reports.

The only change required from your side is start using only port `5050` and instead to use http://localhost:4040/ for rendering Allure report you should use http://localhost:5050/allure-docker-service/latest-report

If you are mounting your volume `-v ${PWD}/allure-results:/app/allure-results` your allure results are being used and stored in `default` project internally in the container, you don't need to change your volume path directory or do anything else. If you want to keep the history reports start to attach another path ` -v ${PWD}/allure-reports:/app/default-reports`.

If you are already using port `4040`, NO WORRIES. The Allure Report exposed in port `4040` will still being rendered for avoiding compatibility problems.
The only issue you will face will be when you try to navigate the HISTORY from the TREND chart or any other widget aiming to any historic data. The error you will see is `HTTP ERROR 404 NOT FOUND`

|       **Version**     |  **Port**  |       **Volume Path**     |  **Container Volume Path**   |                     **Get Latest Report**                    |
|-----------------------|------------|---------------------------|------------------------------|--------------------------------------------------------------|
|  Previous to 2.13.3   |    4040    |   ${PWD}/allure-results   |    /app/allure-results       |   http://localhost:4040/                                     |
|  From 2.13.3          |    5050    |   ${PWD}/allure-results   |    /app/allure-results       |   http://localhost:5050/allure-docker-service/latest-report  |
|                       |            |   ${PWD}/allure-reports   |    /app/default-reports      |                                                              |

Check the new commands to start the container for a single project or for multiple projects: [ALLURE DOCKER SERVICE](#allure-docker-service-1)

### Known Issues
- `Permission denied` --> https://github.com/fescobar/allure-docker-service/issues/108

### Opening & Refreshing Report
If everything was OK, you will see this:
```sh
allure_1  | Generating default report
allure_1  | Overriding configuration
allure_1  | Checking Allure Results every 1 second/s
allure_1  | Creating executor.json for PROJECT_ID: default
allure_1  | Generating report for PROJECT_ID: default
allure_1  | Report successfully generated to /app/allure-docker-api/static/projects/default/reports/latest
allure_1  | Status: 200
allure_1  | Detecting results changes for PROJECT_ID: default
allure_1  | Automatic Execution in Progress for PROJECT_ID: default...
allure_1  | Creating history on results directory for PROJECT_ID: default ...
allure_1  | Copying history from previous results...
allure_1  | Creating executor.json for PROJECT_ID: default
allure_1  | Generating report for PROJECT_ID: default
allure_1  | 2020-06-18 17:02:12.364:INFO::main: Logging initialized @1620ms to org.eclipse.jetty.util.log.StdErrLog
allure_1  | Report successfully generated to /app/allure-docker-api/static/projects/default/reports/latest
allure_1  | Storing report history for PROJECT_ID: default
allure_1  | BUILD_ORDER:1
allure_1  | Status: 200
```

To see your `latest` report simply open your browser and access to:

- http://localhost:5050/allure-docker-service/latest-report

The `latest` report is generated automatically and sometimes could be not available temporary until the new `latest` report has been generated. If you access to the `latest` report url when is not available you will see the `NOT FOUND` page. It will take a few seconds until the latest report be available again.

When you use the `latest-report` will be redirected to the resource url:

- http://localhost:5050/allure-docker-service/projects/default/reports/latest/index.html?redirect=false

When you start the container for a single report, the `default` project will be created automatically, for that reason you are redirected to this endpoint to get information about `default` project, you can see this in the path `.../projects/default/...`

The `redirect=false` parameter is used to avoid be redirected to the `GET /projects/{id}` endpoint (default behaviour)


[![](resources/allure01.png)](resources/allure01.png)

[![](resources/allure02.png)](resources/allure02.png)

[![](resources/allure03.png)](resources/allure03.png)

Now we can run other tests without being worried about Allure server. You don't need to restart or execute any Allure command.

Just go again to this directory [allure-docker-java-testng-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-java-testng-example) via command line:
```sh
cd allure-docker-java-testng-example
```

And execute another suite test:
```sh
mvn test -Dtest=SecondTest
```
When this second test finished, refresh your browser and you will see there is a new report including last results tests.

[![](resources/allure04.png)](resources/allure04.png)

[![](resources/allure05.png)](resources/allure05.png)

We can run the same test suite again and navigate the history:

[![](resources/allure06.png)](resources/allure06.png)

[![](resources/allure07.png)](resources/allure07.png)

[![](resources/allure08.png)](resources/allure08.png)


You can repeat these steps, but now execute the third and fourth test
 ```sh
mvn test -Dtest=ThirdTest
 ```

 ```sh
mvn test -Dtest=FourthTestFactory
 ```

### New User Interface
Check the new UI
- [https://github.com/fescobar/allure-docker-service-ui](https://github.com/fescobar/allure-docker-service-ui)

[![](https://github.com/fescobar/allure-docker-service-ui/blob/master/resources/signin-allure-docker-service-ui.png?raw=true)](https://github.com/fescobar/allure-docker-service-ui/blob/master/resources/signin-allure-docker-service-ui.png?raw=true)

[![](https://github.com/fescobar/allure-docker-service-ui/blob/master/resources/allure-docker-service-ui.png?raw=true)](https://github.com/fescobar/allure-docker-service-ui/blob/master/resources/allure-docker-service-ui.png?raw=true)

### Deploy using Kubernetes
[![](https://github.com/fescobar/allure-docker-service-examples/blob/master/resources/kubernetes.png?raw=true)](https://github.com/fescobar/allure-docker-service-examples/blob/master/resources/kubernetes.png?raw=true)

Check yaml definitions here:
- [allure-docker-kubernetes-example](https://github.com/fescobar/allure-docker-service-examples/tree/master/allure-docker-kubernetes-example)


### Extra options

#### Allure API
Available endpoints:

##### Info Endpoints

`'GET'      /version`

`'GET'      /swagger`

`'GET'      /swagger.json`

##### Action Endpoints

`'GET'      /config`

`'GET'      /latest-report`

`'POST'     /send-results` (admin role)

`'GET'      /generate-report` (admin role)

`'GET'      /clean-results` (admin role)

`'GET'      /clean-history` (admin role)

`'GET'      /emailable-report/render`

`'GET'      /emailable-report/export`

`'GET'      /report/export`


##### Project Endpoints

`'POST'     /projects` (admin role)

`'GET'      /projects`

`'DELETE'   /projects/{id}` (admin role)

`'GET'      /projects/{id}`

`'GET'      /projects/{id}/reports/{path}`

`'GET'      /projects/search`

##### Security Endpoints

`'POST'     /login`

`'POST'     /refresh`

`'DELETE'    /logout`

`'DELETE'    /logout-refresh-token`


Access to http://localhost:5050 to see Swagger documentation with examples

[![](resources/allure-api.png)](resources/allure-api.png)

From version `2.13.4` you can request an endpoint using the base path (prefix) `/allure-docker-service/`:

```sh
curl http://localhost:5050/allure-docker-service/version
```
or you can request without the prefix like in previous versions

```sh
curl http://localhost:5050/version
```

For accessing `Security Endpoints`, you have to enable the security. Check [Enable Security](#enable-security) section.

#### Send results through API
`Available from Allure Docker Service version 2.12.1`

After running your tests, you can execute any script to send the generated results from any node/agent/machine to the Allure Docker server container using the [Allure API](#allure-api). Use the endpoint `POST /send-results`.

You have 2 options to send results:

##### Content-Type - application/json

- Python script: [allure-docker-api-usage/send_results.py](allure-docker-api-usage/send_results.py)

```sh
python send_results.py
```

- Python script with security enabled: [allure-docker-api-usage/send_results_security.py](allure-docker-api-usage/send_results_security.py)

```sh
python send_results_security.py
```

- Declarative Pipeline script for JENKINS: [allure-docker-api-usage/send_results_jenkins_pipeline.groovy](allure-docker-api-usage/send_results_jenkins_pipeline.groovy)

- Declarative Pipeline script for JENKINS with security enabled: [allure-docker-api-usage/send_results_security_jenkins_pipeline.groovy](allure-docker-api-usage/send_results_security_jenkins_pipeline.groovy)


- PowerShell script: [allure-docker-api-usage/send_results.ps1](allure-docker-api-usage/send_results.ps1)

```sh
./send_results.ps1
```

##### Content-Type - multipart/form-data
`Available from Allure Docker Service version 2.13.3`

- Bash script: [allure-docker-api-usage/send_results.sh](allure-docker-api-usage/send_results.sh)

```sh
./send_results.sh
```

- Bash script with security enabled: [allure-docker-api-usage/send_results_security.sh](allure-docker-api-usage/send_results_security.sh)

```sh
./send_results_security.sh
```
NOTE:

- These scripts are sending these example results [allure-docker-api-usage/allure-results-example](allure-docker-api-usage/allure-results-example)

- If you want to clean the results use the endpoint `GET /clean-results` ([Allure API](#allure-api)).

##### Force Project Creation Option
`Available from Allure Docker Service version 2.13.6`
If you use the query parameter `force_project_creation` with value `true`, the project where you want to send the results will be created automatically in case doesn't exist.

`POST /send-results?project_id=any-unexistent-project&force_project_creation=true`

#### Customize Executors Configuration
`Available from Allure Docker Service version 2.13.3`

When you use the `GET /generate-report`, you will see this in your report:

[![](resources/executor00.png)](resources/executor00.png)

If you want to change the `execution name`, you need to pass a parameter named `execution_name` with the value. Example:
`GET /generate-report?execution_name=my-execution-name`

[![](resources/executor01.png)](resources/executor01.png)


If you want to change the `execution from` (by default is empty), you need to pass a parameter named `execution_from` with the value. Example:
`GET /generate-report?execution_from=http://my-jenkins-url/job/my-job/7/`

This option allow you to come back to your executor server.

[![](resources/executor02.png)](resources/executor02.png)


If you want to change the `execution icon` (default is empty), you need to pass a parameter named `execution_type` with the value. Example:
`GET /generate-report?execution_type=jenkins`

If the type is not recognized it will take the default icon. You can use different types like:
- jenkins

[![](resources/executor03.png)](resources/executor03.png)


- teamcity

[![](resources/executor04.png)](resources/executor04.png)


- bamboo

[![](resources/executor05.png)](resources/executor05.png)


- gitlab

[![](resources/executor06.png)](resources/executor06.png)


- github

[![](resources/executor07.png)](resources/executor07.png)


The icons are based on the native Allure2 Framework:
- https://github.com/allure-framework/allure2/tree/master/allure-generator/src/main/javascript/blocks/executor-icon

#### API Response Less Verbose
`Available from Allure Docker Service version 2.13.1`

Enable `API_RESPONSE_LESS_VERBOSE` environment variable if you are handling big quantities of files. This option is useful to avoid to transfer too much data when you request the API. Have in mind the json response structure will change.

```sh
    environment:
      API_RESPONSE_LESS_VERBOSE: 1
```


#### Switching version
You can switch the version container using `frankescobar/allure-docker-service:${VERSION_NUMBER}`.
Docker Compose example:
```sh
  allure:
    image: "frankescobar/allure-docker-service:2.13.8"
```
or using latest version:

```sh
  allure:
    image: "frankescobar/allure-docker-service:latest"
```

By default it will take last version: https://hub.docker.com/r/frankescobar/allure-docker-service/tags

#### Switching port
Inside of the container `Allure API` use port `5050`.
You can switch the port according to your convenience.
Docker Compose example:
```sh
    ports:
      - "9292:5050"
```
#### Updating seconds to check Allure Results
Updating seconds to check `results` directory to generate a new report up to date.
Docker Compose example:
```sh
    environment:
      CHECK_RESULTS_EVERY_SECONDS: 5
```
Use `NONE` value to disable automatic checking results.
If you use this option, the only way to generate a new report up to date it's using the [Allure API](#allure-api).
```sh
    environment:
      CHECK_RESULTS_EVERY_SECONDS: NONE
```

#### Keep History and Trends
`Available from Allure Docker Service version 2.12.1`

Enable `KEEP_HISTORY` environment variable to work with history & trends

Docker Compose example:
```sh
    environment:
      KEEP_HISTORY: "TRUE"
```
From version `2.13.4` you can also use as value `1`
```sh
    environment:
      KEEP_HISTORY: 1
```
 
If you want to clean the history use the [Allure API](#allure-api).

Allure framework allow you to see the latest 20 executions in the history https://github.com/allure-framework/allure2/pull/1059

[![](resources/allure-history-visually-limited-01.png)](resources/allure-history-visually-limited-01.png)

`Available from Allure Docker Service version 2.13.3`

You can access to previous history clicking on the Allure image in the report. If the report is not available you will be redirected to the endpoint `GET /projects/{id}`

[![](resources/allure-history-visually-limited-02.png)](resources/allure-history-visually-limited-02.png)


Also, `Allure Docker Service` by default keeps the latest 20 executions in the history, but you can extend that limit:
```sh
    environment:
      KEEP_HISTORY_LATEST: 28
```

[![](resources/allure-docker-service-history-28.png)](resources/allure-docker-service-history-28.png)


or you can reduce it
```sh
    environment:
      KEEP_HISTORY_LATEST: 10
```

[![](resources/allure-docker-service-history-10.png)](resources/allure-docker-service-history-10.png)

The `latest` directory contains the report from the last execution. On this case, the `29` directory contains the same report in the `latest` directory:

[![](resources/allure-docker-service-history-latest-and-last-execution.png)](allure-docker-service-history-latest-and-last-execution.png)


#### Override User Container
`Available from Allure Docker Service version 2.13.1`

Override the user container in case your platform required it. The container must have permissions to create files inside directories like `allure-results` (Single Project) or `projects` (Multiple Project) or any other directory that you want to mount.

`1000:1000` is the user:group for `allure` user

Docker Compose example:
```sh
    user: 1000:1000
    environment:
      ...
```
or you can pass the current user using environment variable
```sh
    user: ${MY_USER}
    environment:
      ...
```
```sh
MY_USER=$(id -u):$(id -g) docker-compose up -d allure
```

or from Docker you can use parameter `--user`
```sh
docker run --user="$(id -u):$(id -g)" -p 5050:5050 -e CHECK_RESULTS_EVERY_SECONDS=3 -e KEEP_HISTORY="TRUE" \
           -v ${PWD}/allure-results:/app/allure-results \
           -v ${PWD}/allure-reports:/app/default-reports \
           frankescobar/allure-docker-service
```

Note: It's not a good practice to use `root` user to manipulate containers.

Reference: 
- https://snyk.io/blog/10-docker-image-security-best-practices/

#### Start in DEV Mode
`Available from Allure Docker Service version 2.13.3`

Enable dev mode, if you want to see the logs about api requests using the `DEV_MODE` environment variable.

Docker Compose example:
```sh
    environment:
      DEV_MODE: 1
```
NOTE:
- Don't use this mode for live/prod environments.

#### Enable TLS
`Available from Allure Docker Service version 2.13.4`

Enable TLS, if you want to implement `https` protocol using the `TLS` environment variable.

Docker Compose example:
```sh
    environment:
      TLS: 1
```
#### Enable Security
`Available from Allure Docker Service version 2.13.5`

If you are going to publish this API, this feature MUST BE USED TOGETHER with [Enable TLS](#enable-tls), otherwise, your tokens can be intercepted and your security could be vulnerable. When you enable TLS, the cookies credentials will be stored as `SECURE`.

It's recommended to use Allure Docker Service UI container [New User Interface](#new-user-interface) for accessing to the information without credentials problems.

You can define the `ADMIN` user credentials with env vars 'SECURITY_USER' & 'SECURITY_PASS'
Also you need to enable the security to protect the endpoints with env var 'SECURITY_ENABLED'.

Docker Compose example:
```sh
    environment:
      SECURITY_USER: "my_username"
      SECURITY_PASS: "my_password"
      SECURITY_ENABLED: 1
```
Where 'SECURITY_PASS' env var is case sensitive.

Note: Check [Roles](#roles) section if you want to handle different roles.

When the security is enabled, you will see the Swagger documentation (http://localhost:5050/allure-docker-service/swagger) updated with new security endpoints and specifying the protected endpoints.

If you try to use the endpoints `GET /projects`
```sh
curl -X GET http://localhost:5050/allure-docker-service/projects -ik
```

You will see this response
```sh
HTTP/1.1 401 UNAUTHORIZED
Access-Control-Allow-Origin: *
Content-Length: 67
Content-Type: application/json
Date: Tue, 11 Aug 2020 10:31:37 GMT
Server: waitress

{"meta_data":{"message":"Missing cookie \"access_token_cookie\""}}
```

##### Login
To access to protected endpoints you need to use the endpoint `POST /login` with the credentials configured in the initial step.

```sh
curl -X POST http://localhost:5050/allure-docker-service/login \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "my_username",
    "password": "my_password"
}' -c cookiesFile -ik
```
We are storing the cookies obtained in a file `cookiesFile` to use it in the next requests:

Now we try to request the protected endpoints using the cookies obtained from `POST /login` endpoint.
```sh
curl -X GET http://localhost:5050/allure-docker-service/projects -b cookiesFile -ik
```
Using the security cookies we will have access to any endpoint protected.
```sh
HTTP/1.1 200 OK
Access-Control-Allow-Credentials: true
Access-Control-Allow-Origin:
Content-Length: 606
Content-Type: application/json
Date: Sun, 16 Aug 2020 11:09:01 GMT
Server: waitress

{"data":{"projects":{"default":{"uri":"http://localhost:5050/allure-docker-service/projects/default"}}},"meta_data":{"message":"Projects successfully obtained"}}
```

[![](resources/allure_security_login_cookies.png)](resources/allure_security_login_cookies.png)

##### X-CSRF-TOKEN
For example, if you try to create a new project with the security enabled with the cookies obtained in the `POST /login` endpoint

```sh
curl -X POST "http://localhost:5050/allure-docker-service/projects" \
-H "Content-Type: application/json" \
-d '{
  "id": "my-project-id"
}' -b cookiesFile -ik
```
You will received a 401 asking for CSRF token

```sh
HTTP/1.1 401 UNAUTHORIZED
Access-Control-Allow-Credentials: true
Access-Control-Allow-Origin:
Content-Length: 47
Content-Type: application/json
Date: Mon, 17 Aug 2020 07:46:51 GMT
Server: waitress

{"meta_data":{"message":"Missing CSRF token"}}
```

You need to pass the header `X-CSRF-TOKEN` (Cross-Site Request Forgery) if you request to endpoints with method type `POST`, `PUT`, `PATCH` & `DELETE`.

You can get the `X-CSRF-TOKEN` value from the cookie `csrf_access_token` which is obtained from the `POST /login` successfully response (check your cookies section).

Here we are extracting the value of `csrf_access_token` cookie from the `cookiesFile` file generated with the `POST /login`
```sh
CRSF_ACCESS_TOKEN_VALUE=$(cat cookiesFile | grep -o 'csrf_access_token.*' | cut -f2)
echo "csrf_access_token value: $CRSF_ACCESS_TOKEN_VALUE"
```

Once you get the `csrf_access_token` value you need to send it as header named `X-CSRF-TOKEN`

```sh
curl -X POST "http://localhost:5050/allure-docker-service/projects" \
-H "X-CSRF-TOKEN: $CRSF_ACCESS_TOKEN_VALUE" -H "Content-Type: application/json" \
-d '{
  "id": "my-project-id"
}' -b cookiesFile -ik
```

```sh
HTTP/1.1 201 CREATED
Access-Control-Allow-Credentials: true
Access-Control-Allow-Origin:
Content-Length: 90
Content-Type: application/json
Date: Mon, 17 Aug 2020 07:51:37 GMT
Server: waitress

{"data":{"id":"my-project-id"},"meta_data":{"message":"Project successfully created"}}
```

[![](resources/allure_security_create_project_cookies.png)](resources/allure_security_create_project_cookies.png)


##### Refresh Access Token
If you want to avoid the user login each time the access token expired, you need to refresh your token

For refreshing the access token, you have to use the `refresh_token_cookie` and `csrf_refresh_token`

Here, we are extracting the value of `csrf_refresh_token` cookie from the `cookiesFile` file generated with the `POST /login` endpoint
```sh
CRSF_REFRESH_TOKEN_VALUE=$(cat cookiesFile | grep -o 'csrf_refresh_token.*' | cut -f2)
echo "csrf_refresh_token value: $CRSF_REFRESH_TOKEN_VALUE"
```
After that, we need to send `csrf_refresh_token` as header `X-CSRF-TOKEN` and the cookies file with the `-b` option.
```sh
curl -X POST http://localhost:5050/allure-docker-service/refresh -H "X-CSRF-TOKEN: $CRSF_REFRESH_TOKEN_VALUE" -c cookiesFile -b cookiesFile -ik
```
With `-c` options we are overriding the cookies file with the new tokens provided for `POST /refresh` endpoint.
```sh

HTTP/1.1 200 OK
Access-Control-Allow-Credentials: true
Access-Control-Allow-Origin:
Content-Length: 428
Content-Type: application/json
Date: Mon, 17 Aug 2020 08:25:21 GMT
Server: waitress
Set-Cookie: access_token_cookie=eyJ0eXAiOiJKV1Qi...; HttpOnly; Path=/
Set-Cookie: csrf_access_token=d34c2eb1-dcc5-481c-a4ad-2c499a992f65; Path=/

{"data":{"access_token":"eyJ0eXAiOiJKV1Qi..."},"meta_data":{"message":"Successfully token obtained"}}
```

[![](resources/allure_security_refresh_cookies.png)](resources/allure_security_refresh_cookies.png)


The `Access Token` expires in 15 mins by default. You can change the default behaviour with env var `ACCESS_TOKEN_EXPIRES_IN_MINS`

Docker Compose example:
```sh
    environment:
      ACCESS_TOKEN_EXPIRES_IN_MINS: 30
```

Also for development purposes, you can use the env var `ACCESS_TOKEN_EXPIRES_IN_SECONDS`
Docker Compose example:
```sh
    environment:
      ACCESS_TOKEN_EXPIRES_IN_SECONDS: 30
```
You should use the `Refresh Token` to avoid the user login again.

The `Refresh` token doesn't expire by default. You can change the default behaviour with env var `REFRESH_TOKEN_EXPIRES_IN_DAYS`
Docker Compose example:
```sh
    environment:
      REFRESH_TOKEN_EXPIRES_IN_DAYS: 60
```

Also for development purposes you can use the env var `REFRESH_TOKEN_EXPIRES_IN_SECONDS`
Docker Compose example:
```sh
    environment:
      REFRESH_TOKEN_EXPIRES_IN_SECONDS: 10
```

NOTE:
- You can disable the expiration of any token using value 0.

##### Logout
We have 2 endpoints:

With `DELETE /logout` your current `access_token` will be invalidated. You need to pass as header the `csrf_access_token` token.
```sh
CRSF_ACCESS_TOKEN_VALUE=$(cat cookiesFile | grep -o 'csrf_access_token.*' | cut -f2)
echo "csrf_access_token value: $CRSF_ACCESS_TOKEN_VALUE"

curl -X DELETE http://localhost:5050/allure-docker-service/logout -H "X-CSRF-TOKEN: $CRSF_ACCESS_TOKEN_VALUE" -b cookiesFile -ik
```

```sh
HTTP/1.1 200 OK
Access-Control-Allow-Credentials: true
Content-Length: 52
Content-Type: application/json
Date: Fri, 21 Aug 2020 11:17:22 GMT
Server: waitress

{"meta_data":{"message":"Successfully logged out"}}
```

With `DELETE /logout-refresh-token` your current `refresh_token` will be invalidated and all cookies removed. You need to pass as header the `csrf_refresh_token` token:
```sh
CRSF_REFRESH_TOKEN_VALUE=$(cat cookiesFile | grep -o 'csrf_refresh_token.*' | cut -f2)
echo "csrf_refresh_token value: $CRSF_REFRESH_TOKEN_VALUE"

curl -X DELETE http://localhost:5050/allure-docker-service/logout-refresh-token -H "X-CSRF-TOKEN: $CRSF_REFRESH_TOKEN_VALUE" -b cookiesFile -ik
```

```sh
HTTP/1.1 200 OK
Access-Control-Allow-Credentials: true
Content-Length: 52
Content-Type: application/json
Date: Fri, 21 Aug 2020 11:47:47 GMT
Server: waitress
Set-Cookie: access_token_cookie=; Expires=Thu, 01-Jan-1970 00:00:00 GMT; HttpOnly; Path=/
Set-Cookie: csrf_access_token=; Expires=Thu, 01-Jan-1970 00:00:00 GMT; Path=/
Set-Cookie: refresh_token_cookie=; Expires=Thu, 01-Jan-1970 00:00:00 GMT; HttpOnly; Path=/
Set-Cookie: csrf_refresh_token=; Expires=Thu, 01-Jan-1970 00:00:00 GMT; Path=/

{"meta_data":{"message":"Successfully logged out"}}
```

##### Roles
`Available from Allure Docker Service version 2.13.7`

`SECURITY_USER` & `SECURITY_PASS` env vars are used to define the `ADMIN` user credentials who will have access to every endpoint. Also, there is another kind of user just with enough access to check the reports, this is the `VIEWER` user.

You can add this kind of user using `SECURITY_VIEWER_USER` & `SECURITY_VIEWER_PASS` env variables
Docker Compose example:
```sh
    environment:
      SECURITY_USER: "my_username"
      SECURITY_PASS: "my_password"
      SECURITY_VIEWER_USER: "view_user"
      SECURITY_VIEWER_PASS: "view_pass"
      SECURITY_ENABLED: 1
```
Note:
- Always you need to define the `ADMIN` user.
- `SECURITY_USER` & `SECURITY_VIEWER_USER` always need to be different.
- Check [Allure API](#allure-api) to see what endpoints are exclusively for the `ADMIN` role.

##### Make Viewer endpoints public
`Available from Allure Docker Service version 2.13.8`
If you only want to protect the `Admin` endpoints and make public the viewer endpoints, then you can use the environment variable `MAKE_VIEWER_ENDPOINTS_PUBLIC` to make accessible the endpoints:

Docker Compose example:
```sh
    environment:
      SECURITY_USER: "my_username"
      SECURITY_PASS: "my_password"
      SECURITY_ENABLED: 1
      MAKE_VIEWER_ENDPOINTS_PUBLIC: 1
```
Note:
- With `MAKE_VIEWER_ENDPOINTS_PUBLIC` enabled, your `viewer` user (if you have someone defined) won't have effect.

##### Scripts
- Bash script with security enabled: [allure-docker-api-usage/send_results_security.sh](allure-docker-api-usage/send_results_security.sh)
```sh
./send_results_security.sh
```

- Python script with security enabled: [allure-docker-api-usage/send_results_security.py](allure-docker-api-usage/send_results_security.py)

```sh
python send_results_security.py
```

- Declarative Pipeline script for JENKINS with security enabled: [allure-docker-api-usage/send_results_security_jenkins_pipeline.groovy](allure-docker-api-usage/send_results_security_jenkins_pipeline.groovy)


#### Add Custom URL Prefix
`Available from Allure Docker Service version 2.13.5`

Configure an url prefix if your deployment requires it (e.g. reverse proxy with nginx)
```sh
    environment:
      URL_PREFIX: "/my-prefix"
```

With this configuration you can request the API in this way too:
```sh
curl http://localhost:5050/my-prefix/allure-docker-service/version
```

Here's an example config for nginx where `allure` is the name of the docker container
```
server {
    listen 443 ssl;
    ssl_certificate     /certificate.cer;
    ssl_certificate_key /certificate.key;
    location /my-prefix/ {
        proxy_pass http://allure:5050;
        proxy_set_header  Host $host;
        proxy_set_header  X-Real-IP $remote_addr;
        proxy_set_header  X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header  X-Forwarded-Host $server_name;
    }
}
```
NOTE:
- This feature is not supported when DEV_MODE is enabled.

#### Optimize Storage
`Available from Allure Docker Service version 2.13.7`

`---EXPERIMENTAL FEATURE---`

When Allure generates reports, commonly created these files per report:
```sh
projects
   |-- default
   |   |-- results
   |   |-- reports
   |   |   |-- latest
   |   |   |   |-- data
   |   |   |   |-- export
   |   |   |   |-- history
   |   |   |   |-- plugins
   |   |   |   |-- widgets
   |   |   |   |-- favicon.icon
   |   |   |   |-- index.html
   |   |   |   |-- app.js
   |   |   |   |-- styles.css
   |   |   |-- ..
```
The heaviest files are `app.js` & `styles.css`. They never changed their content.
When you enable the option `OPTIMIZE_STORAGE` those files are not stored in your `reports` directory, but they are consumed from a common location inside the container.

Docker Compose example:
```sh
    environment:
      OPTIMIZE_STORAGE: 1
```
Using this feature, your storage consumption will be reduce drastically.

NOTE:
- This feature doesn't have a warranty to work with reports generated with different Allure native versions. For example, if any code is removed from `app.js` or `styles.css` (from a newer version of the native Allure application) that you need to render your reports generated with previous versions, your report couldn't be rendered, you will see a javascript error finding for a component that doesn't exist anymore.


#### Export Native Full Report
`Available from Allure Docker Service version 2.13.1`

You can export the native full report using the endpoint `GET /report/export` [Allure API](#allure-api).

[![](resources/native-full-report.png)](resources/native-full-report.png)



#### Customize Emailable Report
`Available from Allure Docker Service version 2.12.1`

You can render and export the emailable report using the endpoints `GET /emailable-report/render` and `GET ​/emailable-report​/export` [Allure API](#allure-api).

[![](resources/emailable-report.png)](resources/emailable-report.png)

##### Override CSS
By default this report template is using Bootstrap css. If you want to override the css, just you need to pass the enviroment variable `EMAILABLE_REPORT_CSS_CDN`. Docker Compose example:

```sh
    environment:
      EMAILABLE_REPORT_CSS_CDN: "https://stackpath.bootstrapcdn.com/bootswatch/4.3.1/sketchy/bootstrap.css"
```

[![](resources/emailable-report-custom.png)](resources/emailable-report-custom.png)

You can use all these themes: https://bootswatch.com/ or any other boostrap css like https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.css

##### Override title
If you want override the title of the Emailable Report, just you need to pass the environment variable `EMAILABLE_REPORT_TITLE`.

```sh
    environment:
      EMAILABLE_REPORT_TITLE: "My Title"
```

[![](resources/emailable-report-title.png)](resources/emailable-report-title.png)

##### Override server link
`Functionality Deprecated`
- Currently the latest version resolves the host automatically.

---

If you want the Emailable Report to redirect to your Allure server, just you need to pass the environment variable `SERVER_URL`.

```sh
    environment:
      SERVER_URL: "http://my-domain.com/allure-docker-service/latest-report"
```

[![](resources/emailable-report-server-link.png)](resources/emailable-report-server-link.png)


##### Develop a new template
If you want to develop a new template, create a local directory (`my-template` as example) with a file named `default.html`. In that file you can create your own html template, you can use as guide this example: [allure-docker-api/templates/default.html](allure-docker-api/templates/default.html) using [Jinja](https://jinja.palletsprojects.com/en/2.10.x/templates/) syntax. Don't rename your local template, always the file must be named `default.html`.

Mount that directory to the container like in the example and pass the environment variable `FLASK_DEBUG` with value `1`.
This variable will allow you to use `hot reloading`, you can update the content of `default.html` locally and use the endpoint `emailable-report/render` ([Allure API](#allure-api)) to see your changes applied in the browser.

```sh
    environment:
      FLASK_DEBUG: 1
    volumes:
    - ${PWD}/my-template:/app/allure-docker-api/templates
```

#### Allure Customized Plugins
If you want to use your own Allure plugins you can mount your plugin directory
```sh
    environment:
      ...
    volumes:
    - ${PWD}/my-plugin:/allure/plugins/my-plugin
```

References:
- https://docs.qameta.io/allure/#_allure_plugins_system

#### Allure Options
Some frameworks/adaptors don't support allure properties to set up links for `Tracker Management Systems` or `Issue/Bug Trackers`. In that case you need to set up `ALLURE_OPTS` environment variable:
- For Allure1 (XML results)
```sh
    environment:
      CHECK_RESULTS_EVERY_SECONDS: 1
      ALLURE_OPTS: "-Dallure.tests.management.pattern=https://example.org/tms/%s -Dallure.issues.tracker.pattern=https://example.org/issue/%s"
```
- For Allure2 (JSON results). Generally it's not necessary to do this because the properties are configured it in the adaptor/framework and stored in `allure-results` directory. The properties format is different:
```sh
allure.link.mylink.pattern=https://example.org/mylink/{}
allure.link.issue.pattern=https://example.org/issue/{}
allure.link.tms.pattern=https://example.org/tms/{}
```
Reference:
- https://docs.qameta.io/allure/#_test_management_and_bug_tracking_systems_integrations
- https://www.swtestacademy.com/allure-testng/
- https://docs.qameta.io/allure/#_configuration
- https://docs.qameta.io/allure/#_config_samples
- https://docs.qameta.io/allure/#_job_dsl_plugin

## SUPPORT
### Gitter
[![Gitter](https://badges.gitter.im/allure-docker-service/community.svg)](https://gitter.im/allure-docker-service/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)


## DOCKER GENERATION (Usage for developers)
### Install Docker
```sh
sudo apt-get update
```
```sh
sudo apt install -y docker.io
```
If you want to use docker without sudo, read following links:
- https://docs.docker.com/engine/installation/linux/linux-postinstall/#manage-docker-as-a-non-root-user
- https://stackoverflow.com/questions/21871479/docker-cant-connect-to-docker-daemon

### Build image
```sh
docker build -t allure-release -f docker-custom/Dockerfile.bionic-custom --build-arg ALLURE_RELEASE=2.13.8 .
```
### Run container
```sh
docker run -d  -p 5050:5050 allure-release
```
### See active containers
```sh
docker container ls
```
### Access to container
```sh
docker exec -it ${CONTAINER_ID} bash
```
### Access to logs
```sh
docker exec -it ${CONTAINER_ID} tail -f log
```
### Remove all containers
```sh
docker container rm $(docker container ls -a -q) -f
```
### Remove all images
```sh
docker image rm $(docker image ls -a -q)
```
### Remove all stopped containers
```sh
docker ps -q -f status=exited | xargs docker rm
```
### Remove all dangling images
```sh
docker images -f dangling=true | xargs docker rmi
```
### Register tagged image (Example)
```sh
docker login
docker tag allure-release frankescobar/allure-docker-service:${PUBLIC_TAG}
docker push frankescobar/allure-docker-service
```
### Register latest image (Example)
```sh
docker tag allure-release frankescobar/allure-docker-service:latest
docker push frankescobar/allure-docker-service
```
### Download latest image registered (Example)
```sh
docker run -d  -p 5050:5050 frankescobar/allure-docker-service
```
### Download specific tagged image registered (Example)
```sh
docker run -d -p 5050:5050 frankescobar/allure-docker-service:2.13.8
```
