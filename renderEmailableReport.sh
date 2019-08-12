#!/bin/bash

API_CALL=http://localhost:$PORT_API/emailable-report/render
RETRY=7
DELAY=2

$ROOT/retryAPICall.sh $API_CALL $RETRY $DELAY
