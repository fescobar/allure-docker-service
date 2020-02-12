#!/bin/bash

echo "Cleaning results"

if [ "$(ls -A $RESULTS_DIRECTORY | wc -l)" != "0" ]; then
    ls -d $RESULTS_DIRECTORY/* | grep -v history | xargs rm 2> /dev/null
fi

$ROOT/keepAllureHistory.sh
$ROOT/generateAllureReport.sh
$ROOT/renderEmailableReport.sh
