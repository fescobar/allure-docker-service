ARG JDK=eclipse-temurin:11-jre-noble
ARG BUILD_DATE
ARG BUILD_VERSION
ARG BUILD_REF
ARG ALLURE_RELEASE=NONE
ARG ALLURE_REPO=https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline
ARG UID=1000
ARG GID=1000
ARG PYTHON_VERSION=3.13

######

FROM python:${PYTHON_VERSION}-alpine AS dev_stage
RUN apk update
RUN apk add build-base
RUN pip install -U pylint
RUN pip install --upgrade pip==25.2 setuptools==80.9.0 wheel==0.45.1 waitress==3.0.2 && \
    pip install -Iv Flask==3.1.2 Flask-JWT-Extended==4.7.1 flask-swagger-ui==4.11.1 requests==2.32.5

ENV ROOT_DIR=/code
RUN mkdir -p $ROOT_DIR
WORKDIR $ROOT_DIR
COPY allure-docker-api $ROOT_DIR/allure-docker-api
RUN pylint --rcfile=allure-docker-api/.pylintrc allure-docker-api

######
FROM --platform=$BUILDPLATFORM $JDK
ARG JDK
ARG BUILD_DATE
ARG BUILD_VERSION
ARG BUILD_REF
ARG ALLURE_RELEASE
ARG ALLURE_REPO
ARG UID
ARG GID
ARG PYTHON_VERSION=3.13

LABEL org.label-schema.build-date=${BUILD_DATE} \
    org.label-schema.docker.dockerfile="docker/Dockerfile" \
    org.label-schema.license="MIT" \
    org.label-schema.name="Allure Framework" \
    org.label-schema.version=${BUILD_VERSION} \
    org.label-schema.description="Allure Framework is a flexible lightweight multi-language test report tool." \
    org.label-schema.url="https://docs.qameta.io/allure/" \
    org.label-schema.vcs-ref=${BUILD_REF} \
    org.label-schema.vcs-type="Git" \
    org.label-schema.vcs-url="https://github.com/fescobar/allure-docker-service" \
    org.label-schema.arch=${BUILDPLATFORM} \
    authors="Frank Escobar <fescobar.systems@gmail.com>"

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      tzdata \
      nano \
      python${PYTHON_VERSION} \
      unzip && \
    ln -s `which python3` /usr/bin/python && \
    apt-get purge python3-cryptography -y && \
    apt-get autoremove -y && \
    wget https://bootstrap.pypa.io/get-pip.py && \
    sed -i "s/\"--force-reinstall\"/\"--force-reinstall\", \"--break-system-packages\"/g" get-pip.py && \
    python${PYTHON_VERSION} get-pip.py && \
    python${PYTHON_VERSION} -m pip config set global.break-system-packages true && \
    python${PYTHON_VERSION} -m pip install setuptools==80.9.0 wheel==0.45.1 waitress==3.0.2 pipdeptree==2.29.0 cffi==2.0.0 cryptography==46.0.3 && \
    python${PYTHON_VERSION} -m pip install --ignore-installed --upgrade Flask==3.1.2 Flask-JWT-Extended==4.7.1 flask-swagger-ui==4.11.1 requests==2.32.5 && \
    curl ${ALLURE_REPO}/${ALLURE_RELEASE}/allure-commandline-${ALLURE_RELEASE}.zip -L -o /tmp/allure-commandline.zip && \
        unzip -q /tmp/allure-commandline.zip -d / && \
        apt-get remove -y unzip && \
        rm -rf /tmp/* && \
        rm -rf /var/lib/apt/lists/* && \
        chmod -R +x /allure-$ALLURE_RELEASE/bin && \
        mkdir -p /app

RUN usermod -l allure $(getent passwd ${UID} | cut -d: -f1)
RUN mkdir -p /home/allure && \
    chown -R ${UID}:${GID} /home/allure

ENV PYTHON_VERSION=${PYTHON_VERSION}
ENV ROOT=/app
ENV ALLURE_HOME=/allure-$ALLURE_RELEASE
ENV ALLURE_HOME_SL=/allure
ENV PATH=$PATH:$ALLURE_HOME/bin
ENV ALLURE_RESOURCES=$ROOT/resources
ENV RESULTS_DIRECTORY=$ROOT/allure-results
ENV REPORT_DIRECTORY=$ROOT/allure-report
ENV RESULTS_HISTORY=$RESULTS_DIRECTORY/history
ENV REPORT_HISTORY=$REPORT_DIRECTORY/history
ENV ALLURE_VERSION=$ROOT/version
ENV EMAILABLE_REPORT_FILE_NAME='emailable-report-allure-docker-service.html'
ENV STATIC_CONTENT=$ROOT/allure-docker-api/static
ENV STATIC_CONTENT_PROJECTS=$STATIC_CONTENT/projects
ENV DEFAULT_PROJECT=default
ENV DEFAULT_PROJECT_ROOT=$STATIC_CONTENT_PROJECTS/$DEFAULT_PROJECT
ENV DEFAULT_PROJECT_RESULTS=$DEFAULT_PROJECT_ROOT/results
ENV DEFAULT_PROJECT_REPORTS=$DEFAULT_PROJECT_ROOT/reports
ENV EXECUTOR_FILENAME=executor.json

RUN echo -n $(allure --version) > ${ALLURE_VERSION} && \
    echo "ALLURE_VERSION: "$(cat ${ALLURE_VERSION}) && \
    mkdir $ALLURE_HOME_SL && \
    ln -s $ALLURE_HOME/* $ALLURE_HOME_SL && \
    ln -s $STATIC_CONTENT_PROJECTS $ROOT/projects && \
    ln -s $DEFAULT_PROJECT_REPORTS $ROOT/default-reports

WORKDIR $ROOT
COPY --chown=${UID}:${GID} allure-docker-api $ROOT/allure-docker-api
COPY --chown=${UID}:${GID} allure-docker-scripts $ROOT/
RUN chmod +x $ROOT/*.sh && \
    mkdir $RESULTS_DIRECTORY && \
    mkdir -p $DEFAULT_PROJECT_REPORTS/latest && \
    ln -sf $RESULTS_DIRECTORY $DEFAULT_PROJECT_RESULTS && \
    ln -sf $DEFAULT_PROJECT_REPORTS/latest $REPORT_DIRECTORY && \
    allure generate -c -o /tmp/resources && \
    mkdir $ALLURE_RESOURCES && \
    cp /tmp/resources/app.js $ALLURE_RESOURCES && \
    cp /tmp/resources/styles.css $ALLURE_RESOURCES

RUN chown -R ${UID}:${GID} $ROOT

VOLUME [ "$RESULTS_DIRECTORY" ]

ENV DEPRECATED_PORT=4040
ENV PORT=5050

EXPOSE $DEPRECATED_PORT
EXPOSE $PORT

HEALTHCHECK --interval=10s --timeout=60s --retries=3 \
      CMD curl -f http://localhost:$PORT || exit 1

USER allure

CMD $ROOT/runAllureDeprecated.sh & $ROOT/runAllureApp.sh & $ROOT/checkAllureResultsFiles.sh
