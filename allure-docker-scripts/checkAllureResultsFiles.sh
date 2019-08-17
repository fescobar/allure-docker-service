#!/bin/bash

if [ "$CHECK_RESULTS_EVERY_SECONDS" == "NONE" ] || [ "$CHECK_RESULTS_EVERY_SECONDS" == "none" ]; then
	echo "Not checking results automatically"
	while true ; do
		sleep 3600
	done
fi

if echo $CHECK_RESULTS_EVERY_SECONDS | egrep -q '^[0-9]+$'; then
	echo "Overriding configuration"
	SECONDS_TO_WAIT=$CHECK_RESULTS_EVERY_SECONDS
else
	echo "Configuration by default"
	SECONDS_TO_WAIT=1
fi

echo "Checking Allure Results every $SECONDS_TO_WAIT second/s"

detect_changes() {
	FILES="$(echo $(ls $RESULTS_DIRECTORY -Ihistory -l --time-style=full-iso) | md5sum)"
}

sleep 5

while :
do
	detect_changes
	if [ "$FILES" != "$PREV_FILES" ]; then
		echo "Detecting results changes..."
		export env PREV_FILES=$FILES
		$ROOT/keepAllureHistory.sh
		$ROOT/generateAllureReport.sh
		$ROOT/renderEmailableReport.sh
	fi
	sleep $SECONDS_TO_WAIT
done