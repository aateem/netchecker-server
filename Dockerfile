FROM frolvlad/alpine-python2:latest

MAINTAINER Artem Roma version: 0.2

ADD . /usr/src/app/network-checker

WORKDIR /usr/src/app/network-checker

RUN pip install .

ENV NETCHECK server

CMD ["netchecker-server", "0.0.0.0", "8081"]
