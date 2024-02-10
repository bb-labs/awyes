#!/bin/bash

awyes --config-path $1 \
  --client-path $2 \
  --pipfile-path $3 \
  --env-path $4 \
  $5
