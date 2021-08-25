#!/bin/sh

cd /code
poetry install -n
poetry run deploy /github/workspace/"$@"
