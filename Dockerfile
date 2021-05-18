# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9-slim

# +
# https://stackoverflow.com/questions/53835198/integrating-python-poetry-with-docker

ENV PYTHONUNBUFFERED True # Allow statements and log messages to immediately appear in the Knative logs
ENV YOUR_ENV=PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.0.0

RUN pip install --no-cache-dir poetry

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./


RUN poetry && \
    poetry install -v --no-interaction --no-dev --no-ansi
#    poetry config settings.virtualenvs.create false && \

# Install production dependencies.



# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec poetry run python3.9 app.py #gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
