# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.13
ARG BUILD_DATE
ARG BUILD_VERSION
ARG BUILD_REF
ARG ALLURE_NPM_VERSION=3.3.1
ARG UID=1000
ARG GID=1000

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
# Allure CLI: Node oficial (Bookworm) — evita o pacote debian `nodejs`/`npm` com CVEs antigos no Scout.
# `npm audit fix` no pacote `allure` aplica correções semver sem --force (pode falhar silenciosamente).
FROM node:22-bookworm-slim AS allure_cli
ARG ALLURE_NPM_VERSION=3.3.1
RUN apt-get update && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
RUN npm install -g allure@${ALLURE_NPM_VERSION} \
    && ALLURE_PKG="$(npm root -g)/allure" \
    && if [ -f "$ALLURE_PKG/package.json" ]; then (cd "$ALLURE_PKG" && npm audit fix --omit=dev 2>/dev/null || true); fi \
    && npm cache clean --force
# Só binários reais; não copiar o shim `allure` (symlink → ../lib/node_modules/allure/cli.js),
# senão o `import "./dist/index.js"` resolve para /usr/local/bin/dist e falha.
RUN mkdir -p /export/bin /export/lib \
    && cp -a /usr/local/lib/node_modules /export/lib/ \
    && cp -a /usr/local/bin/node /usr/local/bin/npm /usr/local/bin/npx /export/bin/ \
    && allure --version

######
FROM python:${PYTHON_VERSION}-slim-bookworm
ARG PYTHON_VERSION
ARG BUILD_DATE
ARG BUILD_VERSION
ARG BUILD_REF
ARG ALLURE_NPM_VERSION
ARG UID
ARG GID
ARG BUILDPLATFORM=unknown

LABEL org.label-schema.build-date=${BUILD_DATE} \
    org.label-schema.docker.dockerfile="docker/Dockerfile" \
    org.label-schema.license="Apache-2.0" \
    org.label-schema.name="Allure Docker Service" \
    org.label-schema.version=${BUILD_VERSION} \
    org.label-schema.description="Allure Report 3 (npm) with Allure Docker Service API." \
    org.label-schema.url="https://allurereport.org/docs/" \
    org.label-schema.vcs-ref=${BUILD_REF} \
    org.label-schema.vcs-type="Git" \
    org.label-schema.vcs-url="https://github.com/LFBRxD/allure-docker-service" \
    org.label-schema.arch=${BUILDPLATFORM} \
    authors="Flavio Ramos <flavior.desouza@gmail.com> (maintainer); Frank Escobar <fescobar.systems@gmail.com> (original author)" \
    org.opencontainers.image.title="Allure Docker Service" \
    org.opencontainers.image.authors="Flavio Ramos <flavior.desouza@gmail.com> (maintainer); Frank Escobar <fescobar.systems@gmail.com> (original author)" \
    org.opencontainers.image.source="https://github.com/LFBRxD/allure-docker-service" \
    org.opencontainers.image.url="https://github.com/LFBRxD/allure-docker-service" \
    org.opencontainers.image.documentation="https://github.com/LFBRxD/allure-docker-service#readme" \
    org.opencontainers.image.vendor="Flavio Ramos (fork maintainer)" \
    org.opencontainers.image.licenses="Apache-2.0" \
    org.opencontainers.image.description="Allure Report 3 (npm allure): REST API, Swagger, multi-project, report history, report navigator (iframe), emailable HTML reports." \
    org.opencontainers.image.version="${BUILD_VERSION}" \
    org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.revision="${BUILD_REF}" \
    allure.npm.version="${ALLURE_NPM_VERSION}"

RUN apt-get update && apt-get upgrade -y --no-install-recommends \
    && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      procps \
      tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY --from=allure_cli /export/lib/node_modules /usr/local/lib/node_modules
COPY --from=allure_cli /export/bin/node /export/bin/npm /export/bin/npx /usr/local/bin/
RUN ln -sf ../lib/node_modules/allure/cli.js /usr/local/bin/allure \
    && allure --version

RUN groupadd -g ${GID} allure \
    && useradd -u ${UID} -g allure -m -s /bin/sh allure \
    && mkdir -p /home/allure \
    && chown -R ${UID}:${GID} /home/allure

ENV PYTHON_VERSION=${PYTHON_VERSION}
ENV PYTHONUNBUFFERED=1
ENV ROOT=/app
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
ENV ALLURE_REPORT_ENGINE=awesome

WORKDIR $ROOT

COPY NOTICE $ROOT/NOTICE

COPY docker/bootstrap-allure-results /tmp/bootstrap-allure-results

RUN echo -n $(allure --version) > ${ALLURE_VERSION} && \
    echo "ALLURE_VERSION: "$(cat ${ALLURE_VERSION}) && \
    mkdir -p ${ALLURE_RESOURCES} && \
    allure awesome /tmp/bootstrap-allure-results --output /tmp/resources --single-file && \
    rm -rf /tmp/bootstrap-allure-results /tmp/resources && \
    ln -s $STATIC_CONTENT_PROJECTS $ROOT/projects && \
    ln -s $DEFAULT_PROJECT_REPORTS $ROOT/default-reports

COPY --chown=${UID}:${GID} allure-docker-api $ROOT/allure-docker-api
COPY --chown=${UID}:${GID} allure-docker-scripts $ROOT/
RUN chmod +x $ROOT/*.sh && \
    mkdir $RESULTS_DIRECTORY && \
    mkdir -p $DEFAULT_PROJECT_REPORTS/latest && \
    ln -sf $RESULTS_DIRECTORY $DEFAULT_PROJECT_RESULTS && \
    ln -sf $DEFAULT_PROJECT_REPORTS/latest $REPORT_DIRECTORY

RUN python3 -m pip install --no-cache-dir --upgrade pip==25.2 setuptools==80.9.0 wheel==0.45.1 waitress==3.0.2 pipdeptree==2.29.0 cffi==2.0.0 cryptography==46.0.3 && \
    python3 -m pip install --no-cache-dir Flask==3.1.2 Flask-JWT-Extended==4.7.1 flask-swagger-ui==4.11.1 requests==2.32.5

RUN chown -R ${UID}:${GID} $ROOT

VOLUME [ "$RESULTS_DIRECTORY" ]

ENV DEPRECATED_PORT=4040
ENV PORT=5050

EXPOSE $DEPRECATED_PORT
EXPOSE $PORT

HEALTHCHECK --interval=10s --timeout=60s --retries=3 \
      CMD curl -fsS http://127.0.0.1:$PORT/version >/dev/null || exit 1

USER allure

CMD $ROOT/runAllureDeprecated.sh & $ROOT/runAllureApp.sh & $ROOT/checkAllureResultsFiles.sh
