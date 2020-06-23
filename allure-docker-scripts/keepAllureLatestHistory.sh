#!/bin/bash

PROJECT_ID=$1

if [ "$KEEP_HISTORY" == "TRUE" ] || [ "$KEEP_HISTORY" == "true" ] || [ "$KEEP_HISTORY" == "1" ] ; then
    PROJECT_REPORTS_DIRECTORY=$STATIC_CONTENT_PROJECTS/$PROJECT_ID/reports
    KEEP_LATEST="20"
    if echo $KEEP_HISTORY_LATEST | egrep -q '^[0-9]+$'; then
        KEEP_LATEST=$KEEP_HISTORY_LATEST
    fi
    CURRENT_SIZE=$(ls -Ad $PROJECT_REPORTS_DIRECTORY/* | grep -v latest | grep -wv 0 | grep -v $EMAILABLE_REPORT_FILE_NAME | wc -l)

    if [ "$CURRENT_SIZE" -gt "$KEEP_LATEST" ]; then
        SIZE_TO_REMOVE="$(($CURRENT_SIZE-$KEEP_LATEST))"
        echo "Keeping latest $KEEP_LATEST history reports for PROJECT_ID: $PROJECT_ID"
        ls -tAd $PROJECT_REPORTS_DIRECTORY/* | grep -v latest | grep -wv 0 | grep -v $EMAILABLE_REPORT_FILE_NAME | tail -$SIZE_TO_REMOVE | xargs rm 2 -rf> /dev/null
    fi
fi
