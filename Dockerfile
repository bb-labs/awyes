# Container image that runs your code
FROM docker

# Install and link python3
RUN apk add --update python3 py3-pip
RUN ln -sf /usr/bin/python3 /usr/bin/python
RUN ln -sf /usr/bin/pip3 /usr/bin/pip

# Install awyes deps
RUN pip install awyes

COPY . /code

CMD ls -la
