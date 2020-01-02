import os

import pandas as pd
from influxdb_client import InfluxDBClient


def setup_influxdb():
    client = InfluxDBClient(
        url=os.getenv("INFLUXDB_URL"),
        token=os.getenv("INFLUXDB_TOKEN"),
        org=os.getenv("INFLUXDB_ORGANIZATION"),
    )
    return client.query_api()


def get_dataframe(type, duration):
    db = setup_influxdb()

    if type == "all":
        df = db.query_data_frame(
            'from(bucket:"%s") '
            "|> range(start: -%s) "
            '|> filter(fn: (r) => r._field == "value") '
            '|> keep(columns: ["_time", "_measurement", "_value"])'
            % (os.getenv("INFLUXDB_BUCKET"), duration)
        )
    else:
        df = db.query_data_frame(
            'from(bucket:"%s") '
            "|> range(start: -%s) "
            '|> filter(fn: (r) => r._measurement == "%s") '
            '|> filter(fn: (r) => r._field == "value") '
            '|> keep(columns: ["_time", "_measurement", "_value"])'
            % (os.getenv("INFLUXDB_BUCKET"), duration, type)
        )

    df = df.drop(["result", "table"], axis=1)
    df = df.rename(columns={"_time": "time", "_measurement": "type", "_value": "value"})
    df = df.set_index("time")
    df.index = pd.to_datetime(df.index, utc=True).tz_convert("Asia/Tokyo")

    print("Head of generated data frame: %s" % df.head(3))

    return df
