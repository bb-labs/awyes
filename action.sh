#!/bin/sh

cd /deployment
pipenv install --deploy
pipenv run python -m awyes.deployment /github/workspace/"$@"
