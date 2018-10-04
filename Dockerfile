FROM resin/raspberrypi3-alpine-python:2

RUN pip install requests tweepy slackclient
RUN pip install paho-mqtt
RUN pip install --no-cache-dir rpi.gpio

ENTRYPOINT ["python"]


