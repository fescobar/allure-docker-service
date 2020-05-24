#!/bin/bash

EXEC_STORE_RESULTS_PROCESS=$1
PROJECT_ID=$2

# USED FROM API
ORIGIN=$3
EXECUTION_NAME=$4
EXECUTION_FROM=$5
EXECUTION_TYPE=$6

if [ "$KEEP_HISTORY" == "TRUE" ] || [ "$KEEP_HISTORY" == "true" ]; then
    if [[ "$EXEC_STORE_RESULTS_PROCESS" == "1" ]]; then
        $ROOT/storeAllureReport.sh $PROJECT_ID
    fi
fi

echo "Creating $EXECUTOR_FILENAME for PROJECT_ID: $PROJECT_ID"

PROJECT_LATEST_REPORT=$STATIC_CONTENT_PROJECTS/$PROJECT_ID/reports/latest
if [ -e $PROJECT_LATEST_REPORT ]; then
    LAST_REPORT_PATH_DIRECTORY=$(ls -td $STATIC_CONTENT_PROJECTS/$PROJECT_ID/reports/* | grep -v latest | grep -v $EMAILABLE_REPORT_FILE_NAME | head -1)
else
    LAST_REPORT_PATH_DIRECTORY=$(ls -td $STATIC_CONTENT_PROJECTS/$PROJECT_ID/reports/* | grep -v $EMAILABLE_REPORT_FILE_NAME | head -1)
fi

LAST_REPORT_DIRECTORY=$(basename -- "$LAST_REPORT_PATH_DIRECTORY")

RESULTS_DIRECTORY=$STATIC_CONTENT_PROJECTS/$PROJECT_ID/results
if [ ! -d "$RESULTS_DIRECTORY" ]; then
    echo "Creating results directory for PROJECT_ID: $PROJECT_ID"
    mkdir -p $RESULTS_DIRECTORY
fi

EXECUTOR_PATH=$RESULTS_DIRECTORY/$EXECUTOR_FILENAME

if [[ "$LAST_REPORT_DIRECTORY" != "latest" ]]; then
    BUILD_ORDER=$(($LAST_REPORT_DIRECTORY + 1))

    if [ -z "$EXECUTION_NAME" ]; then
        EXECUTION_NAME='Automatic Execution'
    fi

    if [ -z "$EXECUTION_TYPE" ]; then
        EXECUTION_TYPE='another'
    fi

EXECUTOR_JSON=$(cat <<EOF
{
    "reportName": "$PROJECT_ID",
    "buildName": "$PROJECT_ID #$BUILD_ORDER",
    "buildOrder": "$BUILD_ORDER",
    "name": "$EXECUTION_NAME",
    "reportUrl": "../$BUILD_ORDER/index.html",
    "buildUrl": "$EXECUTION_FROM",
    "type": "$EXECUTION_TYPE"
}
EOF
)
    echo $EXECUTOR_JSON > $EXECUTOR_PATH
else
    echo '' > $EXECUTOR_PATH
fi

echo "Generating report for PROJECT_ID: $PROJECT_ID"
allure generate --clean $RESULTS_DIRECTORY -o $STATIC_CONTENT_PROJECTS/$PROJECT_ID/reports/latest

$ROOT/keepAllureLatestHistory.sh $PROJECT_ID
