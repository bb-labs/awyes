FROM python:3.9

WORKDIR /code

COPY . .
# RUN pip3 install pipenv
# RUN pipenv install --deploy
# ENTRYPOINT [ "pipenv", "run", "python", "-m", "awyes.deployment" ]
CMD pwd && ls -la
