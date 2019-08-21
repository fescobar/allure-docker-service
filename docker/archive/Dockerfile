FROM openjdk:8-jdk-slim
LABEL maintainer="fescobar.systems@gmail.com"

ARG RELEASE=NONE
ARG ALLURE_REPO=https://dl.bintray.com/qameta/maven/io/qameta/allure/allure-commandline

RUN apt-get update
RUN apt-get install curl -y
RUN apt-get install vim -y
RUN apt install python-pip -y
RUN pip install Flask flask-swagger-ui requests
RUN apt-get install --reinstall procps -y
RUN apt-get install wget

RUN rm /etc/java-8-openjdk/accessibility.properties
RUN touch /etc/java-8-openjdk/accessibility.properties

RUN wget --no-verbose -O /tmp/allure-$RELEASE.zip $ALLURE_REPO/$RELEASE/allure-commandline-$RELEASE.zip \
  && unzip /tmp/allure-$RELEASE.zip -d / \
  && rm -rf /tmp/*

RUN apt-get remove --auto-remove wget -y

RUN chmod -R +x /allure-$RELEASE/bin

COPY ./allure-docker-api /app/allure-docker-api

ENV ROOT=/app
ENV ALLURE_HOME=/allure-$RELEASE
ENV PATH=$PATH:$ALLURE_HOME/bin
ENV RESULTS_DIRECTORY=$ROOT/allure-results
ENV REPORT_DIRECTORY=$ROOT/allure-report
ENV RESULTS_HISTORY=$RESULTS_DIRECTORY/history
ENV REPORT_HISTORY=$REPORT_DIRECTORY/history
ENV ALLURE_VERSION=$ROOT/version
ENV EMAILABLE_REPORT_DIRECTORY=$ROOT/emailable-report
ENV EMAILABLE_REPORT_HTML=$EMAILABLE_REPORT_DIRECTORY/emailable-report-allure-docker-service.html

RUN echo $(allure --version) > ${ALLURE_VERSION}
RUN echo "ALLURE_VERSION: "$(cat ${ALLURE_VERSION})

WORKDIR $ROOT
ADD *.sh $ROOT/
RUN chmod +x $ROOT/*.sh
RUN mkdir $RESULTS_DIRECTORY
RUN mkdir $REPORT_DIRECTORY
RUN mkdir $EMAILABLE_REPORT_DIRECTORY
RUN echo '<html><head><title>Allure Emailable Report</title></head><body><h3>Initializing Allure Emailable Report...</h3></body></html>' > ${EMAILABLE_REPORT_HTML}

VOLUME [ "$RESULTS_DIRECTORY" ]

ENV PORT=4040
ENV PORT_API=5050

EXPOSE $PORT
EXPOSE $PORT_API

CMD $ROOT/runAllure.sh & $ROOT/runAllureAPI.sh & $ROOT/checkAllureResultsFiles.sh
