""" Inserting TEMPerature into InfluxDB """

import hashlib
import logging
import os
import subprocess
from time import sleep

import schedule
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Logging
formatter = "[%(levelname)-8s] %(asctime)s %(funcName)s %(message)s"
logging.basicConfig(level=logging.INFO, format=formatter)
logger = logging.getLogger(__name__)

# TEMPer
temper_host_name = os.environ["TEMPER_HOST_NAME"]

# InfluxDB
url = os.environ["INFLUXDB_URL"]
token = os.environ["INFLUXDB_TOKEN"]
org = os.environ["INFLUXDB_ORG"]
bucket = os.environ["INFLUXDB_BUCKET"]
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()


class TEMPer:
    def __init__(self):
        self.device_id = hashlib.md5(temper_host_name.encode()).hexdigest()
        self.device_type = "TEMPer"
        self.device_name = "TEMPer via " + temper_host_name

    def __get_temperature(self):
        try:
            result = subprocess.run(
                ["/usr/local/bin/temper"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            temperature = result.stdout.split(",")[1].rstrip("\n")
        except Exception as e:
            logging.error(f"Error: {e}")
            temperature = None

        return temperature

    def get_status(self):
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


if __name__ == "__main__":
    temper = TEMPer()

    schedule.every(5).minutes.do(task, temper)

    while True:
        schedule.run_pending()
        sleep(1)
