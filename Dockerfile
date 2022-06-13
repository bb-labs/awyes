FROM python:3.9

WORKDIR /deployment
COPY . .
RUN pip3 install pipenv
RUN pipenv install --deploy

ENTRYPOINT [ "sh", "/deployment/action.sh" ]