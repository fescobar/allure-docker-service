#!/bin/bash

echo "Cleaning history"
if [ "$(ls -A $REPORT_HISTORY)" ]; then
    rm -r $REPORT_HISTORY/*
fi

if [ -e $RESULTS_HISTORY ]; then
    if [ "$(ls -A $RESULTS_HISTORY)" ]; then
        rm -r $RESULTS_HISTORY/*
    fi
fi

$ROOT/keepAllureHistory.sh
$ROOT/generateAllureReport.sh
$ROOT/renderEmailableReport.sh
