FROM debian:bullseye-slim as builder

RUN apt-get update && apt-get install -y \
    gcc \ 
    make \
    git \
    libusb-1.0 \
    libusb-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/bitplane/temper
COPY temper.c.patch temper/
RUN cd temper \
    && patch --ignore-whitespace < temper.c.patch \
    && make || exit 0 \
    && make install

FROM python:slim-bullseye

RUN apt-get update && apt-get install -y \
    libusb-1.0 \
    libusb-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/bin/temper /usr/local/bin/temper

WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt
COPY temper_influxdb/*.py /app

ENTRYPOINT [ "python", "main.py", "-d" ]
