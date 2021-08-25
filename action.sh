#!/bin/sh

cd /code
echo "$@"
poetry install -n
poetry run deploy "$@"
