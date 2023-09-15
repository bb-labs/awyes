FROM python:3.9

RUN pip3 install awyes


ENTRYPOINT [ "echo", "arg1: $0", "arg2: $1", "all args: $@", "rest: " ]


# ENTRYPOINT "awyes --path /github/workspace/$0 --workflow $1"
