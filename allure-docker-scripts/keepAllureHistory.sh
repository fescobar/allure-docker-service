#!/bin/bash

if [ "$KEEP_HISTORY" == "TRUE" ] || [ "$KEEP_HISTORY" == "true" ]; then
	echo "Creating history on results directory..."
	mkdir -p $RESULTS_HISTORY
	if [ -e $REPORT_HISTORY ]; then
		echo "Copying history from previous results..."
		cp --recursive --preserve=timestamps $REPORT_HISTORY/. $RESULTS_HISTORY
	fi
else
	if [ -d $RESULTS_HISTORY ]; then
		echo "Removing history directory from results..."
		rm -rf $RESULTS_HISTORY;
	fi
fi
