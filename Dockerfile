FROM alpine

# Install and link python3
RUN apk add --update python3 py3-pip
RUN ln -sf /usr/bin/python3 /usr/bin/python
RUN ln -sf /usr/bin/pip3 /usr/bin/pip

# Install awyes deps
RUN pip install awyes

COPY . /code


ENTRYPOINT [ "ls", "-laR", "/" ]
# ENTRYPOINT [ "poetry", "run", "deploy" ]
