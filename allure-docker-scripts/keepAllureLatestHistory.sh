#!/bin/bash

PROJECT_ID=$1

if [ "$KEEP_HISTORY" == "TRUE" ] || [ "$KEEP_HISTORY" == "true" ] || [ "$KEEP_HISTORY" == "1" ] ; then
    PROJECT_REPORTS_DIRECTORY=$STATIC_CONTENT_PROJECTS/$PROJECT_ID/reports
    KEEP_LATEST="20"
    if echo $KEEP_HISTORY_LATEST | egrep -q '^[0-9]+$'; then
        KEEP_LATEST=$KEEP_HISTORY_LATEST
    fi
    # Apenas diretórios com nome numérico (builds); ignorar latest, .html, etc.
    CURRENT_SIZE=$(ls -1 "$PROJECT_REPORTS_DIRECTORY" 2>/dev/null | grep -E '^[0-9]+$' | wc -l)

    if [ "$CURRENT_SIZE" -gt "$KEEP_LATEST" ]; then
        SIZE_TO_REMOVE="$(($CURRENT_SIZE-$KEEP_LATEST))"
        echo "Keeping latest $KEEP_LATEST history reports for PROJECT_ID: $PROJECT_ID"
        ls -1 "$PROJECT_REPORTS_DIRECTORY" 2>/dev/null | grep -E '^[0-9]+$' | sort -n | head -n "$SIZE_TO_REMOVE" | while read -r n; do rm -rf "$PROJECT_REPORTS_DIRECTORY/$n"; done
    fi
fi
