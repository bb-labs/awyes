#!/bin/sh

cd /deployment
pipenv install --deploy
awyes /github/workspace/"$@"
