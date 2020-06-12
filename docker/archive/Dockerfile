FROM openjdk:8-jdk-slim
LABEL maintainer="fescobar.systems@gmail.com"

ARG RELEASE=NONE
ARG ALLURE_REPO=https://dl.bintray.com/qameta/maven/io/qameta/allure/allure-commandline
ARG UID=1000
ARG GID=1000

RUN apt-get update
RUN apt-get install --no-install-recommends -y

RUN apt-get install tzdata -y
RUN apt-get install nano -y
RUN apt-get install curl -y
RUN apt-get install vim -y
RUN apt-get install python3 -y
RUN apt-get install python3-pip -y
RUN apt-get install unzip -y
RUN ln -s `which python3` /usr/bin/python
RUN pip3 install --upgrade pip
RUN pip install -Iv setuptools==47.1.1 wheel==0.34.2
RUN pip install -Iv Flask==1.1.2 flask-swagger-ui==3.25.0 requests==2.23.0
RUN apt-get install --reinstall procps -y
RUN apt-get install wget -y

RUN wget --no-verbose -O /tmp/allure-$RELEASE.zip $ALLURE_REPO/$RELEASE/allure-commandline-$RELEASE.zip \
  && unzip /tmp/allure-$RELEASE.zip -d / \
  && rm -rf /tmp/*

RUN apt-get remove --auto-remove wget -y

RUN groupadd --gid ${GID} allure \
    && useradd --uid ${UID} --gid allure --shell /bin/bash --create-home allure

RUN chmod -R +x /allure-$RELEASE/bin

COPY --chown=allure:allure ./allure-docker-api /app/allure-docker-api

ENV ROOT=/app
ENV ALLURE_HOME=/allure-$RELEASE
ENV ALLURE_HOME_SL=/allure
ENV PATH=$PATH:$ALLURE_HOME/bin
ENV RESULTS_DIRECTORY=$ROOT/allure-results
ENV REPORT_DIRECTORY=$ROOT/allure-report
ENV RESULTS_HISTORY=$RESULTS_DIRECTORY/history
ENV REPORT_HISTORY=$REPORT_DIRECTORY/history
ENV ALLURE_VERSION=$ROOT/version
ENV EMAILABLE_REPORT_FILE_NAME='emailable-report-allure-docker-service.html'
ENV STATIC_CONTENT_PROJECTS=$ROOT/allure-docker-api/static/projects
ENV DEFAULT_PROJECT=default
ENV DEFAULT_PROJECT_ROOT=$STATIC_CONTENT_PROJECTS/$DEFAULT_PROJECT
ENV DEFAULT_PROJECT_RESULTS=$DEFAULT_PROJECT_ROOT/results
ENV DEFAULT_PROJECT_REPORTS=$DEFAULT_PROJECT_ROOT/reports
ENV EXECUTOR_FILENAME=executor.json

RUN echo $(allure --version) > ${ALLURE_VERSION}
RUN echo "ALLURE_VERSION: "$(cat ${ALLURE_VERSION})
RUN mkdir $ALLURE_HOME_SL
RUN ln -s $ALLURE_HOME/* $ALLURE_HOME_SL
RUN ln -s $STATIC_CONTENT_PROJECTS $ROOT/projects
RUN ln -s $DEFAULT_PROJECT_REPORTS $ROOT/default-reports

WORKDIR $ROOT
ADD allure-docker-scripts/*.sh $ROOT/
RUN chmod +x $ROOT/*.sh
RUN mkdir $RESULTS_DIRECTORY
RUN mkdir -p $DEFAULT_PROJECT_REPORTS/latest
RUN ln -sf $RESULTS_DIRECTORY $DEFAULT_PROJECT_RESULTS
RUN ln -sf $DEFAULT_PROJECT_REPORTS/latest $REPORT_DIRECTORY

RUN chown -R allure:allure $ROOT

VOLUME [ "$RESULTS_DIRECTORY" ]

ENV PORT=4040
ENV PORT_API=5050

EXPOSE $PORT
EXPOSE $PORT_API

USER allure

CMD $ROOT/runAllure.sh & $ROOT/runAllureAPI.sh & $ROOT/checkAllureResultsFiles.sh
