#! /bin/bash

if [[ -n "${APP_PATH}" ]]; then
    cd "${APP_PATH}" || exit 1
fi

if [[ X"${1}" = X"bash" ]]; then
    exec bash
else
    exec "$@"
fi
