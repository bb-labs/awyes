FROM python:3.9

RUN pip3 install awyes

CMD awyes --path $1 --workflow $2
