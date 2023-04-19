FROM pytorch/pytorch:1.13.0-cuda11.6-cudnn8-devel

WORKDIR /usr/src
COPY . ./
RUN pip install pika
RUN pip install opencv-python-headless
RUN pip install scipy
RUN pip install matplotlib

CMD [ "python", "./server.py"]