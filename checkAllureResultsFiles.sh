#!/bin/bash
while :
do
	FILES="$(ls $RESULTS_DIRECTORY)"
	if [ "$FILES" != "$PREV_FILES" ]; then
		echo "Detecting new results..."
		/app/generateAllureReport.sh
	fi
	PREV_FILES=$FILES
	export env PREV_FILES=$FILES
	sleep 1
done