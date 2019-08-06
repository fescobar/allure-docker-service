#!/bin/bash

API_CALL=$1
RETRY=$2
DELAY=$3

RETRY_COUNTER=1
while :
	do
		STATUS="$(curl -s -o /dev/null -w "%{http_code}"  $API_CALL)"
		if [ "$STATUS" == "200" ]; then
			echo "Status: $STATUS"
			break;
		fi
		echo "Retrying call $API_CALL in $DELAY seconds"
		sleep $DELAY
		RETRY_COUNTER=$[$RETRY_COUNTER +1]
		if [ "$RETRY_COUNTER" == "$RETRY" ]; then
			echo "Timeout requesting $API_CALL after $RETRY attempts"
			break;
		fi
done
