FROM python:bookworm as builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    libusb-1.0 \
    libusb-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone https://github.com/bitplane/temper
WORKDIR /build/temper
COPY temper.c.patch .
RUN patch --ignore-whitespace < temper.c.patch \
    && make || exit 0 \
    && make install

RUN curl -sSL https://install.python-poetry.org | python3 -

COPY . /build/temper-influxdb
WORKDIR /build/temper-influxdb
RUN "$HOME"/.local/bin/poetry build

FROM python:slim-bookworm

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    libusb-1.0 \
    libusb-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/bin/temper /usr/local/bin/temper
COPY --from=builder /build/temper-influxdb/dist/temper_influxdb-*.whl /tmp
RUN pip install --no-cache-dir /tmp/temper_influxdb-*.whl

ENTRYPOINT [ "temper-influxdb", "-d" ]
