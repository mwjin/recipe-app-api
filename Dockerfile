FROM python:3.10-alpine

ENV PYTHONUNBUFFERED 1

RUN adduser -D user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

RUN pip install --upgrade pip
COPY ./requirements.txt /requirements.txt
USER root
RUN apk add --update --no-cache postgresql-client jpeg-dev
RUN apk add --update --no-cache --virtual .tmp-build-deps \
    gcc libc-dev linux-headers postgresql-dev musl-dev zlib zlib-dev
USER user
RUN pip install -r /requirements.txt
USER root
RUN apk del .tmp-build-deps
RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static
RUN chown -R user:user /vol
RUN chmod -R 755 /vol/web

USER user
RUN mkdir -p /home/user/app
WORKDIR /home/user/app
COPY ./app /app

