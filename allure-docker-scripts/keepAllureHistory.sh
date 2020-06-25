#!/bin/bash

PROJECT_ID=$1
PROJECT_REPORTS_DIRECTORY=$STATIC_CONTENT_PROJECTS/$PROJECT_ID/reports
PROJECT_RESULTS_HISTORY=$STATIC_CONTENT_PROJECTS/$PROJECT_ID/results/history
PROJECT_LATEST_REPORT=$PROJECT_REPORTS_DIRECTORY/latest/history

if [ "$KEEP_HISTORY" == "TRUE" ] || [ "$KEEP_HISTORY" == "true" ] || [ "$KEEP_HISTORY" == "1" ] ; then
	echo "Creating history on results directory for PROJECT_ID: $PROJECT_ID ..."
	mkdir -p $PROJECT_RESULTS_HISTORY
	if [ -e $PROJECT_LATEST_REPORT ]; then
		echo "Copying history from previous results..."
		cp --recursive --preserve=timestamps $PROJECT_LATEST_REPORT/. $PROJECT_RESULTS_HISTORY
	fi
else
	if [ -d $PROJECT_RESULTS_HISTORY ]; then
		echo "Removing history directory from results for PROJECT_ID: $PROJECT_ID ..."
		rm -rf $PROJECT_RESULTS_HISTORY;
	fi
fi
