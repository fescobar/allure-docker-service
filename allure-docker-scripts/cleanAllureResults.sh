#!/bin/bash

PROJECT_ID=$1

echo "Cleaning results for PROJECT_ID: $PROJECT_ID"
PROJECT_RESULTS_DIRECTORY=$STATIC_CONTENT_PROJECTS/$PROJECT_ID/results
if [ "$(ls -A $PROJECT_RESULTS_DIRECTORY | wc -l)" != "0" ]; then
    ls -d $PROJECT_RESULTS_DIRECTORY/* | grep -v history | xargs rm 2> /dev/null
fi

EXEC_STORE_RESULTS_PROCESS=0

$ROOT/keepAllureHistory.sh $PROJECT_ID
$ROOT/generateAllureReport.sh $EXEC_STORE_RESULTS_PROCESS $PROJECT_ID
$ROOT/renderEmailableReport.sh $PROJECT_ID
