FROM python:3.9

RUN pip3 install awyes

COPY action.sh /action.sh

ENTRYPOINT ["/action.sh"]

