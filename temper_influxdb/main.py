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
formatter = "[%(levelname)-8s] %(asctime)s %(funcName)s %(message)s"
logging.basicConfig(level=logging.INFO, format=formatter)
logger = logging.getLogger(__name__)

# TEMPer
TEMPER_PATH = "/usr/local/bin/temper"
temper_host_name = os.getenv("TEMPER_HOST_NAME", os.uname()[1])

# InfluxDB
url = os.environ["INFLUXDB_URL"]
token = os.environ["INFLUXDB_TOKEN"]
org = os.environ["INFLUXDB_ORG"]
bucket = os.environ["INFLUXDB_BUCKET"]
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)


class TEMPer:
    """USB TEMPer device class"""

    def __init__(self):
        self.device_id = hashlib.md5(temper_host_name.encode()).hexdigest()
        self.device_type = "TEMPer"
        self.device_name = "TEMPer via " + temper_host_name

    def __get_temperature(self):
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
            logging.error(f"Error: {e}")
            temperature = None

        return temperature

    def get_status(self):
        """Get device status(temperature)"""
        temperature = self.__get_temperature()

        status = {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "temperature": temperature,
        }

        return status


def save_device_status(status: dict):
    """TEMPerの測定温度をInfluxDBに保存する"""
    if status["temperature"]:
        p = (
            Point(status["device_type"])
            .tag("device_id", status["device_id"])
            .field("temperature", float(status["temperature"]))
        )

        write_api.write(bucket=bucket, record=p)
        logging.info(f"Saved: {status}")
    else:
        logging.error(f"TEMPer Error: {status}")


def task(temper):
    """定期実行するタスク"""
    status = temper.get_status()

    try:
        save_device_status(status)
    except Exception as e:
        logging.error(f"Save error: {e}")


def daemon():
    """Daemon main"""
    temper = TEMPer()

    schedule.every(5).minutes.do(task, temper)

    while True:
        schedule.run_pending()
        sleep(1)


def main():
    """main"""
    temper = TEMPer()
    task(temper)


def cli_main():
    if not os.path.exists(TEMPER_PATH):
        print("Error: please install temper binary - https://github.com/bitplane/temper")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--daemon", action="store_true", help="Daemon mode")
    args = parser.parse_args()
    if args.daemon:
        daemon()
    else:
        main()


if __name__ == "__main__":
    cli_main()
