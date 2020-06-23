# JAVA JUNIT4 DEMO PROJECT USING ALLURE

## INSTALLATION
### JDK8
- http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html

### MAVEN 3.5.4 or latest
- https://maven.apache.org/download.cgi
- https://maven.apache.org/install.html

### Setup JAVA_HOME & M2_HOME
- https://access.redhat.com/documentation/en-us/jboss_enterprise_application_platform/5/html/microcontainer_user_guide/ch01
- https://www.mkyong.com/java/how-to-set-java_home-environment-variable-on-mac-os-x/

Verify installation with:
```sh
java -version
```
```sh
mvn --version
```

## USAGE
Execute Allure Docker Service from this directory
```sh
docker-compose up -d allure
```

- Verify if Allure report is working. Go to -> http://localhost:5050/allure-docker-service/latest-report

Each time you run tests, the Allure report will be updated.
Execute tests:
```sh
mvn test -Dtest=FirstTest
 ```

 ```sh
mvn test -Dtest=SecondTest
 ```

See documentation here: https://github.com/fescobar/allure-docker-service