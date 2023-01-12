FROM python:3-alpine

WORKDIR /usr/src/app
COPY app.py ./
RUN pip install pika

CMD [ "python", "./app.py", "--cfg", "app_cfg.json"]