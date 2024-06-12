# TEMPer - InfluxDB - Grafana

Generate temperature graph using USB TEMPer device

## Usage

### Create .env file

```
cp .env.example .env
```

### Start InfluxDB and Grafana

```
docker compose up influxdb grafana -d
```

### Update InfluxDB Token

Refer created token
```
cat docker/influxdb/config/influx-configs 
```
```
[default]
  url = "http://localhost:8086"
  token = "created_token"
  org = "organization"
  active = true
```

Update .env file
```
vi .env
```
```
INFLUXDB_TOKEN=created_token
```

### Start TEMPer

```
docker compose build
docker compose up temper -d
```
