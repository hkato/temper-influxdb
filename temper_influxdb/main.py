""" Write USB TEMPerature data to InfluxDB """

import argparse
import dataclasses
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


@dataclasses.dataclass
class InfluxDBAccess:
    """InfluxDB access data"""

    url: str
    token: str
    org: str
    bucket: str


class TEMPer:
    """USB TEMPer device class"""

    def __init__(self):
        self.device_id = hashlib.sha1(temper_host_name.encode()).hexdigest()[0:12].upper()
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


def task(influxdb_access, temper) -> None:
    """定期実行するタスク"""
    status = temper.get_status()

    try:
        if status["temperature"]:
            p = (
                Point(status["device_type"])
                .tag("device_id", status["device_id"])
                .field("temperature", float(status["temperature"]))
            )

            client = InfluxDBClient(url=influxdb_access.url, token=influxdb_access.token, org=influxdb_access.org)
            write_api = client.write_api(write_options=SYNCHRONOUS)
            write_api.write(bucket=influxdb_access.bucket, record=p)
            logging.info("Saved: %s", status)
        else:
            logging.error("TEMPer Error: %s", status)

    except Exception as e:
        logging.error("Save error: %s", e)


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

    influxdb_access = InfluxDBAccess(args.url, args.token, args.org, args.bucket)

    logger.info("Start")

    temper = TEMPer()
    task(influxdb_access, temper)

    if args.daemon:
        schedule.every(args.time).minutes.do(task, influxdb_access, temper)
        while True:
            schedule.run_pending()
            sleep(1)


if __name__ == "__main__":
    main()
