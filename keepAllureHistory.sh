#!/bin/bash

if [ "$KEEP_HISTORY" == "TRUE" ] || [ "$KEEP_HISTORY" == "true" ]; then
	mkdir -p $RESULTS_HISTORY
	if [ -e $REPORT_HISTORY ]; then
		echo "Copying history from previous results..."
		cp -a $REPORT_HISTORY/. $RESULTS_HISTORY
	fi
fi
