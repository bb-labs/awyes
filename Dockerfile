FROM python:3.9

RUN pip3 install awyes

ENTRYPOINT [ "awyes", "/github/workspace/$1" ]
