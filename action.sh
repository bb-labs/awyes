#!/bin/bash

awyes --config /github/workspace/$1 \
  --clients /github/workspace/$2 \
  --env /github/workspace/$3 \
  --workflow $4
