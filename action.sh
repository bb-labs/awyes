#!/bin/sh

cd /deployment
pipenv run python -m awyes.deployment /github/workspace/"$@"
