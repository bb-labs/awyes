FROM python:3.9

RUN apt-get update && \
    apt-get -y install sudo

RUN pip3 install awyes

COPY action.sh /action.sh

ENTRYPOINT ["/action.sh"]

