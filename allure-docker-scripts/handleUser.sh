#!/usr/bin/env bash

# This script is used within the OpenShift image to handle account restrictions

if ! whoami &> /dev/null; then
    if [[ -w /etc/passwd ]]; then
        echo "${USER_NAME:-default}:x:$(id -u):0:${USER_NAME:-default} user:/home/${USER_NAME:-default}:/bin/bash" >> /etc/passwd
    fi
    if [[ ! -d /home/${USER_NAME:-default} ]] ; then
        mkdir -p /home/${USER_NAME:-default}
        chown -R ${USER_NAME:-default}:0 /home/${USER_NAME:-default}
    fi
fi
