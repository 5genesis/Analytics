"""
Module to connect to InfluxDB and retrieve data for analytics.
"""


__author__ = 'Erik Aumayr'


from influxdb import DataFrameClient
import urllib
import pandas as pd
from tqdm import tqdm
import requests
from io import BytesIO


class DataCollector:

    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        try:
            self.client = DataFrameClient(host, port, user, password, database, timeout=30)
            self.client.ping()
            self.experimentIds = self.cache_experimentIds()
        except requests.exceptions.ConnectTimeout as e:  # Timeout of InfluxDB connection
            print(e)
            self.client = None


    def get_data(self, experimentId, measurements=[], fields=[], additional_clause=None, chunked=False, chunk_size=10000, limit=None, offset=None, max_lag="1s"):
        if not measurements:
            results = self.client.query(f"SHOW measurements WHERE (ExperimentId =~ /{experimentId}/ or ExecutionId =~ /{experimentId}/)")
            measurements = [item["name"] for item in results["measurements"]]
        measurements = ", ".join([f'"{item}"' for item in measurements])
        fields = ', '.join([f'"{item}"' for item in fields]) if fields else '*'
        limit = f' LIMIT {limit}' if limit else ''
        offset = f' OFFSET {offset}' if offset else ''
        if not additional_clause:
            additional_clause = ''
        df = self.query_df(f'SELECT {fields} FROM {measurements} WHERE (ExperimentId =~ /{experimentId}/ or ExecutionId =~ /{experimentId}/){additional_clause}{limit}{offset}')
        df = df.set_index('time')
        df.index = pd.to_datetime(df.index).floor(max_lag)
        df = df.mean(level=0)  # .dropna(axis=0)
        return df


    def get_experimentIds_for_measurement(self, measurement):
        result = self.client.query(f'SELECT distinct(ExecutionId) as ExecutionId from (SELECT * from "{measurement}")', chunked=False, chunk_size=1000, epoch='ns')
        return list(result[measurement].iloc[:, 0])


    def get_measurements_for_experimentId(self, experimentId):
        result = self.client.query(f'SHOW measurements WHERE ExecutionId =~ /{experimentId}/ or ExperimentId =~ /{experimentId}/', chunked=False, chunk_size=1000, epoch='ns')
        return [item["name"] for item in list(result['measurements'])]


    def cache_experimentIds(self):
        experimentIds = []
        measurements = [measurement['name'] for measurement in self.client.get_list_measurements()]
        for measurement in tqdm(measurements, desc="Getting ExecutionIds"):
            results = self.query_df(f'''SELECT distinct(ExecutionId) as ExecutionId from (SELECT * from "{measurement}")''')
            if not results.empty:
                experimentIds += list(results['ExecutionId'].astype(str))
        return sorted(list(set(experimentIds)))


    def query_df(self, query):
        data = {}
        data['db'] = self.database
        data['u'] = self.user
        data['p'] = self.password
        data['precision'] = 'ns'
        data['q'] = query
        url_values = urllib.parse.urlencode(data)
        url = f"http://{self.host}:{self.port}/query?" + url_values
        request = urllib.request.Request(url, headers={'Accept': 'application/csv'})
        response = urllib.request.urlopen(request)
        response_bytestr = response.read()
        if response_bytestr:
            return pd.read_csv(BytesIO(response_bytestr), sep=",", low_memory=False)
        else:
            return pd.DataFrame()


    def get_all_experimentIds(self):
        return self.experimentIds


if __name__ == '__main__':
    import getpass
    host = input("Host: ")
    port = input("Port: ")
    database = input("Database: ")
    user = input("User: ")
    password = getpass.getpass()
    server = DataCollector(host, port, user, password, database)
    data = server.get_data("101_1", measurements=["ADB_Resource_Agent"], limit=3)
    for series_name, series in data.items():
        print('\n', series_name)
        print(series)
