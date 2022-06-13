FROM python:3.9

WORKDIR /deployment

COPY . .
# RUN pip3 install pipenv
# RUN pipenv install --deploy
# ENTRYPOINT [ "pipenv", "run", "python", "-m", "awyes.deployment" ]
RUN cd /deployment
CMD ls -la
