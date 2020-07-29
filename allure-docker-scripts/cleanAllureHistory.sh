#!/bin/bash

PROJECT_ID=$1
EXEC_STORE_RESULTS_PROCESS=0

echo "Cleaning history for PROJECT_ID: $PROJECT_ID"
PROJECT_REPORTS_DIRECTORY=$STATIC_CONTENT_PROJECTS/$PROJECT_ID/reports
PROJECT_RESULTS_HISTORY=$STATIC_CONTENT_PROJECTS/$PROJECT_ID/results/history
EXECUTOR_PATH=$STATIC_CONTENT_PROJECTS/$PROJECT_ID/results/$EXECUTOR_FILENAME
PROJECT_LATEST_REPORT=$PROJECT_REPORTS_DIRECTORY/latest

if [ "$(ls -A $PROJECT_LATEST_REPORT | wc -l)" != "0" ]; then
    rm -rf $PROJECT_LATEST_REPORT/*
fi

if [ "$(ls -A $PROJECT_REPORTS_DIRECTORY | wc -l)" != "0" ]; then
    ls -d $PROJECT_REPORTS_DIRECTORY/* | grep -v latest | grep -wv 0 | xargs rm 2 -rf> /dev/null
fi

if [ -e $PROJECT_RESULTS_HISTORY ]; then
    if [ "$(ls -A $PROJECT_RESULTS_HISTORY | wc -l)" != "0" ]; then
        rm -rf $PROJECT_RESULTS_HISTORY/*
    fi
fi

if [ -e $EXECUTOR_PATH ]; then
    echo '' > $EXECUTOR_PATH
fi

if [ "$CHECK_RESULTS_EVERY_SECONDS" != "NONE" ] && [ "$CHECK_RESULTS_EVERY_SECONDS" != "none" ]; then
    $ROOT/keepAllureHistory.sh $PROJECT_ID
    $ROOT/generateAllureReport.sh $EXEC_STORE_RESULTS_PROCESS $PROJECT_ID
    $ROOT/renderEmailableReport.sh $PROJECT_ID
fi

echo "History cleaned for PROJECT_ID: $PROJECT_ID"
