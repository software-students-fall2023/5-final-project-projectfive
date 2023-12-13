FROM python:3.12.1-slim-bookworm

COPY /Pipfile .
COPY /Pipfile.lock .

RUN pip install pipenv
RUN apt-get update
RUN apt-get install -y llvm-dev
RUN pipenv install --system --deploy --verbose

COPY /app .

# NOTE: You have to mount a directory containing cert.pem and key.pem to /certs.
CMD ["python", "app.py"]