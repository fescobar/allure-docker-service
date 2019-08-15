#!/bin/bash

echo "Cleaning results"
if [ "$(ls -A $RESULTS_DIRECTORY)" ]; then
    find $RESULTS_DIRECTORY/* ! -name history -delete
fi

$ROOT/keepAllureHistory.sh
$ROOT/generateAllureReport.sh
$ROOT/renderEmailableReport.sh
