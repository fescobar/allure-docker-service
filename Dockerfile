FROM openjdk:8-jdk-slim
LABEL maintainer="fescobar.systems@gmail.com"

ARG RELEASE=NONE
ARG ALLURE_REPO=https://dl.bintray.com/qameta/maven/io/qameta/allure/allure-commandline

RUN apt-get update
RUN apt-get install curl -y
RUN apt-get install vim -y
RUN apt install python-pip -y
RUN pip install Flask
RUN apt-get install --reinstall procps -y
RUN apt-get install wget

RUN rm /etc/java-8-openjdk/accessibility.properties
RUN touch /etc/java-8-openjdk/accessibility.properties

RUN wget --no-verbose -O /tmp/allure-$RELEASE.zip $ALLURE_REPO/$RELEASE/allure-commandline-$RELEASE.zip \
  && unzip /tmp/allure-$RELEASE.zip -d / \
  && rm -rf /tmp/*

RUN apt-get remove --auto-remove wget -y

RUN chmod -R +x /allure-$RELEASE/bin

COPY allure-docker-api /app/allure-docker-api

ENV ALLURE_HOME=/allure-$RELEASE
ENV PATH=$PATH:$ALLURE_HOME/bin
ENV RESULTS_DIRECTORY=/app/allure-results
ENV REPORT_DIRECTORY=/app/allure-report
ENV RESULTS_HISTORY=$RESULTS_DIRECTORY/history
ENV REPORT_HISTORY=$REPORT_DIRECTORY/history
ENV ALLURE_VERSION=/app/version

RUN echo $(allure --version) > ${ALLURE_VERSION}
RUN echo "ALLURE_VERSION: "$(cat ${ALLURE_VERSION})

WORKDIR /app
ADD *.sh /app/
RUN chmod +x /app/*.sh
RUN mkdir $RESULTS_DIRECTORY
RUN mkdir $REPORT_DIRECTORY

VOLUME [ "$RESULTS_DIRECTORY" ]

ENV PORT=4040
ENV PORT_API=5050

EXPOSE $PORT
EXPOSE $PORT_API

CMD /app/runAllure.sh & /app/runAllureAPI.sh & /app/checkAllureResultsFiles.sh
