#!/bin/bash

awyes --config /github/workspace/$1 \
  --clients /github/workspace/$2 \
  --deps /github/workspace/$3 \
  --env /github/workspace/$4 \
  --workflow $5
