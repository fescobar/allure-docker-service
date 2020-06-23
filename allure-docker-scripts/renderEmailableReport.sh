#!/bin/bash
PROJECT_ID=$1

API_CALL=http://localhost:$PORT/allure-docker-service/emailable-report/render?project_id=$PROJECT_ID
RETRY=7
DELAY=2

$ROOT/retryAPICall.sh $API_CALL $RETRY $DELAY
