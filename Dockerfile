FROM python:3.9

WORKDIR /code
RUN pip3 install pipenv

COPY . .
RUN pipenv install --deploy
ENTRYPOINT [ "pipenv", "run", "python", "-m", "awyes.deployment" ]
