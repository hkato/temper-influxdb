""" Inserting TEMPerature into InfluxDB """

import argparse
import hashlib
import logging
import os
import subprocess
import sys
from time import sleep

import schedule
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Logging
FORMATTER = "[%(levelname)-8s] %(asctime)s %(funcName)s %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMATTER)
logger = logging.getLogger(__name__)

# TEMPer
TEMPER_PATH = os.getenv("TEMPER_PATH", "/usr/local/bin/temper")
temper_host_name = os.getenv("TEMPER_HOST_NAME", os.uname()[1])


class InfluxDB:
    """InfluxDB Client"""

    url: str
    token: str
    org: str
    bucket: str

    def get_client(self) -> InfluxDBClient:
        """Get InfluxDBClient"""
        client = InfluxDBClient(url=self.url, token=self.token, org=self.org)

        return client

    def save_device_status(self, status: dict) -> None:
        """TEMPerの測定温度をInfluxDBに保存する"""
        if status["temperature"]:
            p = (
                Point(status["device_type"])
                .tag("device_id", status["device_id"])
                .field("temperature", float(status["temperature"]))
            )

            write_api = self.get_client().write_api(write_options=SYNCHRONOUS)

            write_api.write(bucket=self.bucket, record=p)
            logging.info("Saved: %s", status)
        else:
            logging.error("TEMPer Error: %s", status)


class TEMPer:
    """USB TEMPer device class"""

    def __init__(self):
        self.device_id = hashlib.md5(temper_host_name.encode()).hexdigest()
        self.device_type = "TEMPer"
        self.device_name = "TEMPer via " + temper_host_name

    def get_temperature(self) -> float:
        """Get temperature from temper binary"""
        try:
            result = subprocess.run(
                [TEMPER_PATH],
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            temperature = result.stdout.split(",")[1].rstrip("\n")
        except Exception as e:
            logging.error("Error: %s", e)
            temperature = None

        return temperature

    def get_status(self) -> dict:
        """Get device status(temperature)"""
        temperature = self.get_temperature()

        status = {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "temperature": temperature,
        }

        return status


def task(influx, temper) -> None:
    """定期実行するタスク"""
    status = temper.get_status()

    try:
        influx.save_device_status(status)
    except Exception as e:
        logging.error("Save error: %s", e)


def daemon(influx, time: int) -> None:
    """Daemon main"""
    logger.info("Start")
    temper = TEMPer()

    schedule.every(time).minutes.do(task, influx, temper)

    while True:
        schedule.run_pending()
        sleep(1)


def onetime(influx) -> None:
    """main"""
    temper = TEMPer()
    task(influx, temper)


def main():
    """CLI main"""
    if not os.path.exists(TEMPER_PATH):
        print("Error: please install temper binary - https://github.com/bitplane/temper")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--daemon", action="store_true", help="Daemon mode")
    parser.add_argument("-t", "--time", default=5, help="Time interval", type=int)
    parser.add_argument("--url", default=os.getenv("INFLUXDB_URL"), help="InfluxDB URL")
    parser.add_argument("--token", default=os.getenv("INFLUXDB_TOKEN"), help="InfluxDB token")
    parser.add_argument("--org", default=os.getenv("INFLUXDB_ORG"), help="InfluxDB organization")
    parser.add_argument("--bucket", default=os.getenv("INFLUXDB_BUCKET"), help="InfluxDB bucket")
    args = parser.parse_args()

    # InfluxDB
    influx = InfluxDB()
    influx.url = args.url
    influx.token = args.token
    influx.org = args.org
    influx.bucket = args.bucket

    if args.daemon:
        daemon(influx, args.time)
    else:
        onetime(influx)


if __name__ == "__main__":
    main()
