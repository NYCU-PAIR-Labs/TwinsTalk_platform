FROM pytorch/pytorch:1.13.0-cuda11.6-cudnn8-devel

WORKDIR /usr/src/app
COPY server.py ./
COPY SmartFall_lstm.pth ./
RUN pip install pika
RUN pip install pika

CMD [ "python", "./server.py"]