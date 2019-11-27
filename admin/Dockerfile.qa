FROM ubuntu:18.04

RUN \
  apt update && \
  apt-get install -y make gcc-5 g++-5 python3 python3-pip && \
  apt-get clean

WORKDIR /gcovr
COPY requirements.txt .
COPY doc/requirements.txt doc/

ENV PYTHON=python3 CC=gcc-5 CXX=g++-5 GCOV=gcov-5

RUN \
  $PYTHON -m pip install --no-cache-dir --upgrade pip && \
  $PYTHON -m pip install --no-cache-dir -r requirements.txt -r doc/requirements.txt

CMD $PYTHON -m pip install -e . && make qa
