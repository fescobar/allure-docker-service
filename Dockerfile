FROM openjdk:10.0-jdk-slim
LABEL maintainer="fescobar.systems@gmail.com"

ARG ALLURE_VERSION=allure-2.7.0

RUN apt-get update
RUN apt-get install tar
RUN apt-get install vim -y

COPY $ALLURE_VERSION.tgz /
RUN tar -xvf $ALLURE_VERSION.tgz
RUN chmod -R +x /$ALLURE_VERSION/bin

ENV ALLURE_HOME=/$ALLURE_VERSION
ENV PATH=$PATH:$ALLURE_HOME/bin
ENV RESULTS_DIRECTORY=/app/allure-results
ENV REPORT_DIRECTORY=/app/allure-report
ENV PREV_FILES=
RUN allure --version

WORKDIR /app
ADD runAllure.sh /app
ADD generateAllureReport.sh /app
ADD checkAllureResultsFiles.sh /app
RUN mkdir $RESULTS_DIRECTORY
RUN mkdir $REPORT_DIRECTORY

VOLUME [ "$RESULTS_DIRECTORY" ]

ENV PORT=4040
EXPOSE $PORT

CMD /app/runAllure.sh & /app/checkAllureResultsFiles.sh