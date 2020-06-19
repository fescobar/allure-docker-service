#!/bin/bash
echo "ALLURE_VERSION:" $(cat ${ALLURE_VERSION})
EXEC_STORE_RESULTS_PROCESS=0
PROJECT_ID='default'

if [ -e $REPORT_DIRECTORY/index.html ]; then
	echo "Opening existing report"
else
	echo "Generating default report"
	$ROOT/generateAllureReport.sh $EXEC_STORE_RESULTS_PROCESS $PROJECT_ID
	$ROOT/renderEmailableReport.sh $PROJECT_ID
fi
allure open --port $DEPRECATED_PORT > /tmp/log_deprecated_port
