#!/bin/bash
PROJECT_ID=$1

ENDPOINT="http://localhost:$PORT/allure-docker-service/emailable-report/render?project_id=$PROJECT_ID"
RETRY=7
DELAY=2
COOKIES_TEMP_FILE=""
AUTH=0

if [ "$SECURITY_ENABLED" == "1" ] && [ -n "$SECURITY_USER" ] && [ -n "$SECURITY_PASS" ]; then
	AUTH=1
fi

if [ "$AUTH" == "1" ]; then
	COOKIES_TEMP_FILE=$(tempfile)
    curl -X POST http://localhost:$PORT/login -H 'Content-Type: application/json' -d '{ "username": "'$SECURITY_USER'", "password": "'$SECURITY_PASS'"}' -c $COOKIES_TEMP_FILE --silent --output /dev/null --show-error --fail
fi

RETRY_COUNTER=1
while :
	do
		if [ "$AUTH" == "1" ]; then
            STATUS="$(curl -LI $ENDPOINT -b $COOKIES_TEMP_FILE -o /dev/null -w '%{http_code}\n' -s)"
        else
			STATUS="$(curl -LI $ENDPOINT -o /dev/null -w '%{http_code}\n' -s)"
        fi

		if [ "$STATUS" == "200" ]; then
			echo "Status: $STATUS"
			break;
		fi

		echo "Retrying call $ENDPOINT in $DELAY seconds"
		sleep $DELAY
		RETRY_COUNTER=$[$RETRY_COUNTER +1]
		if [ "$RETRY_COUNTER" == "$RETRY" ]; then
			echo "Timeout requesting $API_CALL after $RETRY attempts"
			break;
		fi
done

if [ -n "$COOKIES_TEMP_FILE" ]; then
	rm $COOKIES_TEMP_FILE
fi
