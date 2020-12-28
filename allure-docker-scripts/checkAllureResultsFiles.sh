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

declare -A RESULTS
declare -A PREV_RESULTS

detect_changes(){
    for PROJECT_ID in $(ls $STATIC_CONTENT_PROJECTS) ; do
        RESULTS_DIR=$STATIC_CONTENT_PROJECTS/$PROJECT_ID/results
        if [ -d "$RESULTS_DIR" ]; then
            RESULTS[$PROJECT_ID]="$(echo $(ls $RESULTS_DIR -Ihistory -I$EXECUTOR_FILENAME -lH --time-style=full-iso) | md5sum)"
        else
            unset RESULTS[$PROJECT_ID]
        fi
    done
}

sleep 5

EXEC_STORE_RESULTS_PROCESS=1

while :
do
    detect_changes
    for KEY in "${!RESULTS[@]}" ; do
        #echo "$KEY > ${RESULTS[$KEY]}"
        if [ "${RESULTS[$KEY]}" != "${PREV_RESULTS[$KEY]}" ]; then
            echo "Detecting results changes for PROJECT_ID: $KEY"
            API_PROCESSES_SIZE=$(ps -fea | grep -w $KEY | grep -w api | wc -l)
            if [ "$API_PROCESSES_SIZE" -le "0" ]; then
                echo "Automatic Execution in Progress for PROJECT_ID: $KEY..."
                PREV_RESULTS[$KEY]=${RESULTS[$KEY]}
                $ROOT/keepAllureHistory.sh $KEY
                $ROOT/generateAllureReport.sh $EXEC_STORE_RESULTS_PROCESS $KEY
                $ROOT/renderEmailableReport.sh $KEY
            else
                echo "API Processes in progress for PROJECT_ID: $KEY - Automatic Execution Postponed"
            fi
        fi
    done
    sleep $SECONDS_TO_WAIT
done
