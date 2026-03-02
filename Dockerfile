FROM python:3.12-alpine
LABEL maintainer="Konstantin-SVT"

WORKDIR app/

RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
RUN mkdir -p fixtures

RUN adduser --no-create-home --disabled-password django-user
USER django-user