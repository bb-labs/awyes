#!/bin/bash

awyes --config-path /github/workspace/$1 \
  --client-path /github/workspace/$2 \
  --pipfile-path /github/workspace/$3 \
  --env-path /github/workspace/$4 \
  $5
