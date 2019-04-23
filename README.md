[![](images/allure.png)](http://allure.qatools.ru/)
[![](images/docker.png)](https://docs.docker.com/)

# ALLURE DOCKER SERVICE
Table of contents
=================
   * [FEATURES](#FEATURES)
   * [USAGE](#USAGE)
      * [Generate Allure Results](#generate-allure-results)
      * [Allure Docker Service](#allure-docker-service-1)
          * [Using Docker on Unix/Mac](#using-docker-on-unixmac)
          * [Using Docker on Windows (Git Bash)](#using-docker-on-windows-git-bash)
          * [Using Docker Compose](#using-docker-compose)
      * [Opening & Refreshing Report](#opening--refreshing-report)
      * [Extra options](#extra-options)
          * [Allure Generate Report Endpoint](#allure-generate-report-endpoint)
          * [Changing port](#changing-port)
          * [Updating seconds to check Allure Results](#updating-seconds-to-check-allure-results)
   * [DOCKER GENERATION (Usage for developers)](#docker-generation-usage-for-developers)

## FEATURES
Allure Framework provides you good looking reports for automation testing.
For using this tool it's required to install a server. You could have this server running on Jenkins or if you want to see reports locally you need run some commands on your machine. This work results tedious, at least for me :)

For that reason this docker container allows you to see updated reports simply mounting your `allure-results` directory in the container. Every time appears new results (generated for your tests), Allure Docker Service will detect those new results files and it will generate a new report automatically (optional: generate report on demand via API), what you will see refreshing your browser.

It's useful even for developers who wants to run tests locally and want to see what were the problems during regressions.

## USAGE
### Generate Allure Results
First at all it's important to be clear. This container only generates reports based on results. You have to generate allure results according to the technology what are you using.

We have some examples projects:
- [allure-docker-java-testng-example](allure-docker-java-testng-example)
- [allure-docker-java-cucumber-jvm-example](allure-docker-java-cucumber-jvm-example)
- [allure-docker-nodejs-example](allure-docker-nodejs-example)
- [allure-docker-nodejs-typescript-example](allure-docker-nodejs-typescript-example)
- [AllureDockerCSharpExample](AllureDockerCSharpExample)

In this case we are going to generate results using the java project [allure-docker-java-testng-example](allure-docker-java-testng-example) of this repository.

Go to directory [allure-docker-java-testng-example](allure-docker-java-testng-example) via command line:

```sh
cd allure-docker-java-testng-example
```
Execute:

```sh
mvn test -Dtest=FirstTestNGAllureTest
```
If everything is OK, you should see something like this:

```sh
[INFO] -------------------------------------------------------
[INFO]  T E S T S
[INFO] -------------------------------------------------------
[INFO] Running com.allure.docker.FirstTestNGAllureTest
SLF4J: Failed to load class "org.slf4j.impl.StaticLoggerBinder".
SLF4J: Defaulting to no-operation (NOP) logger implementation
SLF4J: See http://www.slf4j.org/codes.html#StaticLoggerBinder for further details.
test1
test2
[ERROR] Tests run: 2, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 2.419 s <<< FAILURE! - in com.allure.docker.FirstTestNGAllureTest
[ERROR] test2(com.allure.docker.FirstTestNGAllureTest)  Time elapsed: 0.042 s  <<< FAILURE!
java.lang.AssertionError: ERROR DURING THE TEST
        at com.allure.docker.FirstTestNGAllureTest.test2(FirstTestNGAllureTest.java:42)

[INFO] 
[INFO] Results:
[INFO] 
[ERROR] Failures: 
[ERROR]   FirstTestNGAllureTest.test2:42 ERROR DURING THE TEST
[INFO] 
[ERROR] Tests run: 2, Failures: 1, Errors: 0, Skipped: 0
[INFO] 
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
```

There are 2 tests, one of them failed. Now you can see the `allure-results` diretory was created inside of [allure-docker-java-testng-example](allure-docker-java-testng-example) project.

Just it has left 1 step more. You have to run `allure-docker-service` mounting your `allure-results` directory.

### Allure Docker Service
Docker Image: https://hub.docker.com/r/frankescobar/allure-docker-service/

#### Using Docker on Unix/Mac
From this directory [allure-docker-java-testng-example](allure-docker-java-testng-example) execute next command:
```sh
docker run -p 4040:4040 -p 5050:5050 -e CHECK_RESULTS_EVERY_SECONDS=3 -v ${PWD}/allure-results:/app/allure-results frankescobar/allure-docker-service
```

#### Using Docker on Windows (Git Bash)
From this directory [allure-docker-java-testng-example](allure-docker-java-testng-example) execute next command:
```sh
docker run -p 4040:4040 -p 5050:5050 -e CHECK_RESULTS_EVERY_SECONDS=3 -v "/$(pwd)/allure-results:/app/allure-results" frankescobar/allure-docker-service
```

#### Using Docker Compose
Using docker-compose is the best way to manage containers: [allure-docker-java-testng-example/docker-compose.yml](allure-docker-java-testng-example/docker-compose.yml)

```sh
version: '3'

  allure:
    image: "frankescobar/allure-docker-service"
    environment:
      CHECK_RESULTS_EVERY_SECONDS: 1
    ports:
      - "4040:4040"
      - "5050:5050"
    volumes:
      - "${PWD}/allure-results:/app/allure-results"
```

From this directory [allure-docker-java-testng-example](allure-docker-java-testng-example) execute next command:

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
- The `${PWD}/allure-results` directory could be in anywhere on your machine. Your project must generate results in that directory.
- The `/app/allure-results` directory is inside of the container. You MUST NOT change this directory, otherwise, the container won't detect the new changes.

### Opening & Refreshing Report
If everything was OK, you will see this:
```sh
Overriding configuration
Checking Allure Results every 1 second/s
Detecting new results...
Generating report
  * Serving Flask app "app" (lazy loading)
  * Environment: production
    WARNING: Do not use the development server in a production environment.
    Use a production WSGI server instead.
  * Debug mode: off
  * Running on http://0.0.0.0:5050/ (Press CTRL+C to quit)
2.10.0
Generating default report
Generating report
Report successfully generated to allure-report
Report successfully generated to allure-report
Starting web server...
2019-02-07 12:22:23.820:INFO::main: Logging initialized @204ms to org.eclipse.jetty.util.log.StdErrLog
Can not open browser because this capability is not supported on your platform. You can use the link below to open the report manually.
Server started at <http://172.22.0.2:4040/>. Press <Ctrl+C> to exit
```

All previous examples started the container using port 4040. Simply open your browser and access to: 

http://localhost:4040

[![](images/allure01.png)](images/allure01.png)

[![](images/allure02.png)](images/allure02.png)

[![](images/allure03.png)](images/allure03.png)

Now we can run other tests without being worried about Allure server. You don't need to restart or execute any Allure command.

Just go again to this directory [allure-docker-java-testng-example](allure-docker-java-testng-example) via command line:
```sh
cd allure-docker-java-testng-example
```

And execute another suite test:
```sh
mvn test -Dtest=SecondTestNGAllureTest
```
When this second test finished, refresh your browser and you will see there is a new report including last results tests.

[![](images/allure04.png)](images/allure04.png)

[![](images/allure05.png)](images/allure05.png)

### Extra options

#### Allure Generate Report Endpoint
This endpoint is useful to force to generate a new report on demand.

Request:
```sh
curl -X GET http://localhost:5050/generate-report -ik
```
Response:
```sh
{
    "data": {
        "allure_results_files": [
            "240dbfaa-de15-4c48-addc-31c2c5861c3f-container.json",
            "314127b2-ff70-433c-9db7-534c31b773a9-result.json",
            "4f90ba22-b6b5-4979-8d4e-e36a80a4c725-result.json",
            "6d2270f8-6961-4ad5-9b81-af59b6a57116-container.json",
            "9b0d11a5-8c23-402f-be52-2818ae1db765-attachment",
            "baee6435-a109-4f1d-bc94-8c3132111c92-attachment.mp4",
            "d4e54580-5d61-4aa9-b5e9-af76d1c42a2f-container.json",
            "d79cb78e-287e-457f-8a03-5eb1482d2073-container.json",
            "ddaf6d54-910b-4895-8f9a-4029a952d3c8-container.json",
            "e183e26b-cbbf-459b-91fa-d0648036cc8c-result.json",
            "fd53d71d-3551-4ea2-90fd-639e507aa59e-container.json",
            "fd71f6e7-3d4a-4a14-be54-324bd519e408-result.json"
        ]
    },
    "meta_data": {
        "message": "Report generated successfully"
    }
}
```

Failed response:
You are not allowed to execute this request more than 1 time consecutively. You will have to wait for this process to finish to execute this request again.
```sh
{
    "meta_data": {
        "message": "'Generating Report' process is running currently. Try later!"
    }
}
```

#### Changing port
Inside of the container `Allure Report` use port `4040` and `Allure API` use port `5050`.
You can change those ports according to your convenience. Docker Compose example:
```sh
    ports:
      - "8484:4040"
      - "9292:5050"
```
#### Updating seconds to check Allure Results
Updating seconds to check `allure-results` directory to generate a new report up to date. Docker Compose example:
```sh
    environment:
      CHECK_RESULTS_EVERY_SECONDS: 5
```
Use `NONE` value to disable automatic checking results.
If you use this option, the only way to generate a new report updated it's using the API [Allure Generate Report Endpoint](#allure-generate-report-endpoint), requesting on demand.
```sh
    environment:
      CHECK_RESULTS_EVERY_SECONDS: NONE
```

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
docker build -t allure-release .
```
### Run container
```sh
docker run -d -p 4040:4040 -p 5050:5050 allure-release
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
docker run -d -p 4040:4040 -p 5050:5050 frankescobar/allure-docker-service
```
### Download specific tagged image registered (Example)
```sh
docker run -d -p 4040:4040 -p 5050:5050 frankescobar/allure-docker-service:2.10.0
```