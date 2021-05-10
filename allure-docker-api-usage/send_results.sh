#!/bin/bash

function usage() {
  echo "usage: send_results_security.py [-h] -r RESULTS_DIR -a ALLURE_SERVER [-p] [-f]
                                [-j] [-s] [--username] [--password] [--no-ssl]
                                [-c] [-g] [--exec-name] [--exec-from]
                                [--exec-type]

Upload the test results to the Allure Docker Service

required arguments:
  -r RESULTS_DIR, --results-dir RESULTS_DIR
                        Directory path to where the results are stored locally
  -a ALLURE_SERVER, --allure-server ALLURE_SERVER
                        URL pointing to the Allure Service e.g.
                        http://localhost:5050

optional arguments:
  -h, --help            show this help message and exit
  -p , --project        The project ID to upload the results for
  -f, --force           Set if you want to force the creation of the project
  -j, --json            Set if you want to send all of the results as json
                        data
  -s, --secure          Set if the Allure Docker Service is configure with
                        access credentials
  --username            Username for the Allure Service
  --password            Password for the Allure Service
  --no-ssl              Set if you do not want to verify SSL
  -c, --compress        Set if you want to compress the results before sending
  -g, --generate        Set if you want to generate the report after uploading
                        the results
  --exec-name           Name of the test execution
  --exec-from           URL pointing to the execution
  --exec-type           Execution type e.g. Jenkins, GitLab etc"
  exit 0
}

PROJECT='default'
FORCE=0
JSON=0
COMPRESS=0
SECURE=0
SSL=1
GENERATE=0

while (( "$#" )); do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    -r|--results-dir)
      RESULTS_DIR=$2
      shift 2
      ;;
    -a|--allure-server)
      ALLURE_SERVER=$2
      shift 2
      ;;
    -p|--project)
      PROJECT=$2
      shift 2
      ;;
    -f|--force)
      FORCE=1
      shift 1
      ;;
    -j|--json)
      JSON=1
      shift 1
      ;;
    -s|--secure)
      SECURE=1
      shift 1
      ;;
    --username)
      USERNAME=$2
      shift 2
      ;;
    --password)
      PASSWORD=$2
      shift 2
      ;;
    --no-ssl)
      SSL=0
      shift 1
      ;;
    -c|--compress)
      COMPRESS=1
      shift 1
      ;;
    -g|--generate)
      GENERATE=1
      shift 1
      ;;
    --exec-name)
      EXEC_NAME=$2
      shift 2
      ;;
    --exec-from)
      EXEC_FROM=$2
      shift 2
      ;;
    --exec-type)
      EXEC_TYPE=$2
      shift 2
      ;;
    *)
      echo "Warning: Unsupported argument $1"
      exit 0
  esac
done


( [ -z $RESULTS_DIR ] || [ -z $ALLURE_SERVER ] ) && usage
[ $SECURE == 1 ] && ( [ -z $USERNAME ] || [ -z $PASSWORD ] ) && echo "-s, --secure requires --username and --password" && exit 255
[ $COMPRESS == 1 ] && [ $JSON == 1 ] && echo "-j, --json and -c,--compress cannot be used together" && exit 255
( [ ! -z $EXEC_FROM ] || [ ! -z $EXEC_NAME ] || [ ! -z $EXEC_TYPE ] ) && [ $GENERATE == 0 ] && echo "--exec-name, --exec-from and --exec-type cannot be used if -g,--generate is not set" && exit 255

if [[ $COMPRESS == 1 ]]; 
then
  zip /tmp/results.zip $RESULTS_DIR/*
  FILES=" -F files[]=@/tmp/results.zip"
else
  FILES_TO_SEND=$(ls -dp $RESULTS_DIR/* | grep -v /$)
  if [ -z "$FILES_TO_SEND" ]; then
    exit 1
  fi
  FILES=''
  for FILE in $FILES_TO_SEND; do
    FILES+=" -F files[]=@$FILE "
  done
fi

URL="$ALLURE_SERVER/allure-docker-service/send-results?project_id=$PROJECT"

if [[ $FORCE == 1 ]]
then
  URL+="&force_project_creation=true"
fi

set -o xtrace

SEND_RESULTS_CMD="curl -X POST $URL -i"

if [[ $SECURE == 1 ]]
then
  echo "------------------LOGIN-----------------"
  curl -X POST "$ALLURE_SERVER/allure-docker-service/login" \
    -H 'Content-Type: application/json' \
    -d "{
      "\""username"\"": "\""$USERNAME"\"",
      "\""password"\"": "\""$PASSWORD"\""
  }" -c cookiesFile -ik

  echo "------------------EXTRACTING-CSRF-ACCESS-TOKEN------------------"
  CRSF_ACCESS_TOKEN_VALUE=$(cat cookiesFile | grep -o 'csrf_access_token.*' | cut -f2)
  echo "csrf_access_token value: $CRSF_ACCESS_TOKEN_VALUE"

  SEND_RESULTS_CMD+=" -H 'X-CSRF-TOKEN: $CRSF_ACCESS_TOKEN_VALUE' -b cookiesFile"
fi

if [[ $JSON == 1 ]]; then
  JSON_STRING='{"results":['

  FILES_TO_ENCODE=$(ls -dp $RESULTS_DIR/* | grep -v /$)

  for FILE in $FILES_TO_ENCODE; do
    BASE64_CONTENT=$(base64 $FILE)
    FILENAME=$(basename $FILE)
    JSON_STRING+='{"file_name": "'$FILENAME'", "content_base64": "'$BASE64_CONTENT'"},'
  done

  JSON_STRING=${JSON_STRING: : -1}
  JSON_STRING+=']}'

  SEND_RESULTS_CMD+=" -H 'Content-Type: application/json'"
  SEND_RESULTS_CMD+=" -d '$JSON_STRING'"
else
  SEND_RESULTS_CMD+=" -H 'Content-Type: multipart/form-data'"
  SEND_RESULTS_CMD+=$FILES
fi

eval $SEND_RESULTS_CMD

if [[ $GENERATE == 1 ]]
then
  URL="$ALLURE_SERVER/allure-docker-service/generate-report?project_id=$PROJECT"

  if [[ ! -z $EXEC_FROM ]]
  then
    URL+="&execution_from=$EXEC_FROM"
  fi

  if [[ ! -z $EXEC_NAME ]]
  then
    URL+="&execution_name=$EXEC_NAME"
  fi

  if [[ ! -z $EXEC_TYPE ]]
  then
    URL+="&execution_type=$EXEC_TYPE"
  fi

  if [[ $SECURE==1 ]]
  then
    RESPONSE=$(curl -X GET $URL \
    -H "X-CSRF-TOKEN: $CRSF_ACCESS_TOKEN_VALUE" \
    -b cookiesFile)
  else
    RESPONSE=$(curl -X GET $URL)
  fi

  REPORT_URL=$(echo $RESPONSE | grep -o 'http.*\.html')
  echo "The generated report can be accessed on: $REPORT_URL"

fi