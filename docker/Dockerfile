ARG BUILD_DATE
ARG BUILD_VERSION
ARG BUILD_REF
ARG ALLURE_RELEASE=2.44.0
ARG ALLURE_REPO=https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline
ARG UID=1000
ARG GID=1000

######

FROM python:3.13-alpine@sha256:540c7d91f98ff6880174c40e99067bf5941eb54d818a7a5e094d188b196a934d AS dev_stage
RUN apk update && apk upgrade && \
    apk add --no-cache build-base
RUN pip install --no-cache-dir -U pylint
RUN pip install --no-cache-dir --upgrade pip==26.2.1 setuptools==83.0.0 wheel==0.46.2 waitress==3.0.2 && \
    pip install --no-cache-dir -Iv Flask==3.1.3 Flask-JWT-Extended==4.7.1 flask-swagger-ui==4.11.1 requests==2.33.0

ENV ROOT_DIR=/code
RUN mkdir -p $ROOT_DIR
WORKDIR $ROOT_DIR
COPY allure-docker-api $ROOT_DIR/allure-docker-api
RUN pylint --rcfile=allure-docker-api/.pylintrc allure-docker-api

######
FROM python:3.13-alpine@sha256:540c7d91f98ff6880174c40e99067bf5941eb54d818a7a5e094d188b196a934d
ARG BUILD_DATE
ARG BUILD_VERSION
ARG BUILD_REF
ARG ALLURE_RELEASE=2.44.0
ARG ALLURE_REPO=https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline
ARG UID=1000
ARG GID=1000

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
    authors="Frank Escobar <fescobar.systems@gmail.com>"

RUN apk update && apk upgrade && \
    apk add --no-cache \
      bash \
      curl \
      tzdata \
      shadow \
      ca-certificates \
      openjdk11-jre-headless \
      unzip && \
    ln -sf /bin/mktemp /usr/bin/tempfile && \
    ln -sf $(which python3) /usr/bin/python && \
    ln -sf $(which python3) /usr/bin/python3 && \
    pip install --no-cache-dir --upgrade pip==26.2.1 setuptools==83.0.0 wheel==0.46.2 waitress==3.0.2 pipdeptree==2.29.0 cffi==2.0.0 cryptography==50.0.0 && \
    pip install --no-cache-dir --ignore-installed --upgrade Flask==3.1.3 Flask-JWT-Extended==4.7.1 flask-swagger-ui==4.11.1 requests==2.33.0 && \
    curl -fsSL ${ALLURE_REPO}/${ALLURE_RELEASE}/allure-commandline-${ALLURE_RELEASE}.zip -o /tmp/allure-commandline.zip && \
    unzip -q /tmp/allure-commandline.zip -d / && \
    curl -fsSL https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-databind/2.22.1/jackson-databind-2.22.1.jar -o /tmp/jackson-databind-2.22.1.jar && \
    curl -fsSL https://repo1.maven.org/maven2/org/jsoup/jsoup/1.23.1/jsoup-1.23.1.jar -o /tmp/jsoup-1.23.1.jar && \
    find /allure-${ALLURE_RELEASE} -name "jackson-databind-*.jar" -exec cp /tmp/jackson-databind-2.22.1.jar {} \; && \
    find /allure-${ALLURE_RELEASE} -name "jsoup-*.jar" -exec cp /tmp/jsoup-1.23.1.jar {} \; && \
    apk del unzip && \
    rm -rf /tmp/* /var/cache/apk/* /root/.cache /usr/local/lib/python3.13/site-packages/pip/_vendor/bom.cdx.json && \
    chmod -R +x /allure-$ALLURE_RELEASE/bin && \
    mkdir -p /app

RUN if getent passwd ${UID} >/dev/null 2>&1; then \
      usermod -l allure $(getent passwd ${UID} | cut -d: -f1); \
    else \
      useradd -u ${UID} -U -d /home/allure -s /bin/bash allure; \
    fi && \
    mkdir -p /home/allure && \
    chown -R ${UID}:${GID} /home/allure

ENV PYTHON_VERSION=""
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
    mkdir -p $ALLURE_RESOURCES && \
    APP_FILE=$(find /tmp/resources -type f \( -name "app.js" -o -name "index.js" -o -name "*.js" \) | head -n 1) && \
    CSS_FILE=$(find /tmp/resources -type f \( -name "styles.css" -o -name "index.css" -o -name "*.css" \) | head -n 1) && \
    if [ -n "$APP_FILE" ]; then cp "$APP_FILE" $ALLURE_RESOURCES/app.js; else touch $ALLURE_RESOURCES/app.js; fi && \
    if [ -n "$CSS_FILE" ]; then cp "$CSS_FILE" $ALLURE_RESOURCES/styles.css; else touch $ALLURE_RESOURCES/styles.css; fi

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
