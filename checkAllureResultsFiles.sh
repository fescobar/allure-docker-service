#!/bin/bash

if echo $CHECK_RESULTS_EVERY_SECONDS | egrep -q '^[0-9]+$'; then
	echo "Overriding configuration"
	SECONDS_TO_WAIT=$CHECK_RESULTS_EVERY_SECONDS
else
	echo "Configuration by default"
	SECONDS_TO_WAIT=1
fi

echo "Checking Allure Results each $SECONDS_TO_WAIT second/s"

while :
do
	FILES="$(ls $RESULTS_DIRECTORY -l --time-style=full-iso)"
	if [ "$FILES" != "$PREV_FILES" ]; then
		echo "Detecting new results..."
		/app/generateAllureReport.sh
	fi
	PREV_FILES=$FILES
	export env PREV_FILES=$FILES
	sleep $SECONDS_TO_WAIT
done