FROM python:3.9

RUN pip3 install awyes

CMD ls -l

ENTRYPOINT "awyes --path /github/workspace/$0 --workflow $1"
