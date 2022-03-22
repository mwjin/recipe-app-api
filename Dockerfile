FROM python:3.10-alpine

ENV PYTHONUNBUFFERED 1

RUN adduser -D user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

RUN pip install --upgrade pip
COPY ./requirements.txt /requirements.txt
USER root
RUN apk add --update --no-cache postgresql-client
RUN apk add --update --no-cache --virtual .tmp-build-deps \
    gcc libc-dev linux-headers postgresql-dev
USER user
RUN pip install -r /requirements.txt
USER root
RUN apk del .tmp-build-deps
USER user

RUN mkdir -p /home/user/app
WORKDIR /home/user/app
COPY ./app /app

