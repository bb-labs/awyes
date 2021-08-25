FROM alpine

# Install and link python3
RUN apk add --update --no-cache \
  python3 \
  py3-pip \
  libressl-dev \
  musl-dev \
  libffi-dev \
  openssl-dev \
  py-cryptography

# Install poetry to run awyes
RUN pip3 install poetry

# Symlink to python3
RUN ln -sf /usr/bin/python3 /usr/bin/python
RUN ln -sf /usr/bin/pip3 /usr/bin/pip

# Move code
COPY . /code

# Make script executable
# RUN chmod +x /code/action.sh

ENTRYPOINT [ "ls -laR /" ]
