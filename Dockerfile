FROM python:3.10-alpine

ENV PYTHONUNBUFFERED 1

RUN adduser -D user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

RUN pip install --upgrade pip
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir -p /home/user/app
WORKDIR /home/user/app
COPY ./app /app

