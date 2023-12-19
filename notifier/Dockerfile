FROM python:3.12.1-slim-bookworm

COPY /Pipfile .
COPY /Pipfile.lock .

RUN pip install pipenv
RUN apt-get update
RUN apt-get install -y python-setuptools
RUN pipenv install --system --deploy --verbose

COPY /notifier .

CMD ["python", "notifier.py"]