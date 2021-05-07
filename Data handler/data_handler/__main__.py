__author__ = 'Erik Aumayr'

from os import environ
from datetime import datetime
from flask import Flask, request
import json
import yaml
import pandas as pd
from data_handler.collect_data import DataCollector
from data_handler.time_series_matching import synchronize
from data_handler.outlier_detection import remove


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return {'about': "Data handler for 5Genesis Analytics Component. Visit /help for more info."}, 200


@app.route('/help')
@app.route('/API')
@app.route('/api')
def get_help():
    response = {
        "/get_datasources": "no parameters",
        "/get_all_experimentIds/datasource": "no parameters",
        "/get_experimentIds_for_measurement/datasource/measurement": "no parameters",
        "/get_measurements_for_experimentId/datasource/experimentId": "no parameters",
        "/get_data/datasource/experimentId1(/experimentId2)": {
            "default parameters": {
                'measurement': "None (individual measurement name, e.g. Throughput_Measures)",
                'field': "None (field filter, e.g. Throughput (Mbps))",
                'additional_clause': "None (any InfluxDB clause)",
                'chunked': "False (or True)",
                'chunk_size': "10000 (any integer)",
                'match_series': "False (or True)",
                'remove_outliers': "None (zscore or mad)",
                'limit': "None (any integer)",
                'offset': "None (any integer)",
                'max_lag': "1s (time lag for synchronisation)"
            },
            'datasource': "uma, athens_iperf, athens_rtt"
        }
    }
    return response, 200


@app.route("/purge_cache", methods=["GET"])
def purge_cache():
    global data_cache
    data_cache = {}
    return {"message": "Cache purged"}, 200


@app.route("/get_datasources", methods=["GET"])
def get_datasources():
    return {"sources": list(sources.keys())}, 200


@app.route("/get_all_experimentIds/<string:datasource>", methods=["GET"])
def get_all_executionIds(datasource):
    if datasource not in sources or not sources[datasource].client:
        return {"error": f"Data source {datasource} is not available."}, 404
    experimentIds = getattr(sources[datasource], "get_all_experimentIds")()
    return {f"ExperimentIds on {datasource}": experimentIds}, 200


@app.route('/get_experimentIds_for_measurement/<string:datasource>/<string:measurement>', methods=['GET'])
def get_excutionIds(datasource, measurement):
    if datasource not in sources or not sources[datasource].client:
        return {"error": f"Data source {datasource} is not available."}, 404
    experimentIds = getattr(sources[datasource], "get_experimentIds_for_measurement")(measurement)
    return {f"ExperimentIds for measurement {measurement} on {datasource}": experimentIds}, 200


@app.route('/get_measurements_for_experimentId/<string:datasource>/<string:experimentId>', methods=['GET'])
def get_measurements(datasource, experimentId):
    if datasource not in sources or not sources[datasource].client:
        return {"error": f"Data source {datasource} is not available."}, 404
    measurements = getattr(sources[datasource], "get_measurements_for_experimentId")(experimentId)
    return {f"Measurements for experimentId {experimentId} on {datasource}": measurements}, 200


def retrieve_data(datasource, experimentId, measurements=[], fields=[], match_series=False, remove_outliers=None, additional_clause=None, chunked=False, chunk_size=10000, limit=None, offset=None, max_lag='1s'):
    start = datetime.now()
    if datasource not in sources or not sources[datasource].client:
        return None
    dataid = str(datasource) + str(experimentId) + ''.join(sorted(measurements)) + str(fields) + str(remove_outliers) + str(match_series) + str(additional_clause) + str(max_lag) + str(limit)
    if enable_cache:
        global data_cache
        if dataid not in data_cache:
            print('-- Retrieving uncached data', flush=True)
            data = getattr(sources[datasource], "get_data")(experimentId, measurements=measurements, fields=fields, additional_clause=additional_clause, chunked=chunked, chunk_size=chunk_size, limit=limit, offset=offset, max_lag=max_lag)
            data_cache[dataid] = data
        else:
            print('-- Using cached data', flush=True)
            data = data_cache[dataid]
    else:
        data = getattr(sources[datasource], "get_data")(experimentId, measurements=measurements, fields=fields, additional_clause=additional_clause, chunked=chunked, chunk_size=chunk_size, limit=limit, offset=offset, max_lag=max_lag)
    if match_series:
        data = synchronize(dataframes=data, max_lag=max_lag, merge=True)
    if remove_outliers:
        if remove_outliers.lower() == 'zscore':
            data = remove(data, 0)
        if remove_outliers.lower() == 'mad':
            data = remove(data, 1)
    print(datetime.now() - start, flush=True)
    return data


@app.route('/get_data/<string:datasource>/<string:experimentId1>', methods=['GET'], defaults={'experimentId2': None})
@app.route('/get_data/<string:datasource>/<string:experimentId1>/<string:experimentId2>', methods=['GET'])
def get_data(datasource, experimentId1, experimentId2):
    measurements = request.args.getlist('measurement')
    fields = request.args.getlist('field')
    additional_clause = request.args.get('additional_clause')
    chunked = request.args.get('chunked')
    chunked = chunked.lower() == 'true' if chunked else False
    chunk_size = request.args.get('chunk_size')
    chunk_size = int(chunk_size) if chunk_size else 10000
    match_series = request.args.get('match_series')
    match_series = match_series.lower() == 'true' if match_series else False
    remove_outliers = request.args.get('remove_outliers')  # zscore, mad or None
    limit = request.args.get('limit')
    if limit:
        limit = int(limit)
    offset = request.args.get('offset')
    if offset:
        offset = int(offset)
    max_lag = request.args.get('max_lag', '1s')
    if not experimentId2:
        data = retrieve_data(datasource, experimentId1, measurements, fields, match_series, remove_outliers, additional_clause, chunked, chunk_size, limit, offset, max_lag)
        if type(data) == pd.DataFrame and data.empty or type(data) == dict and data == {}:
            return {"error": f"Data source {datasource} is currently not available."}, 404
        jsonobjects = {name: json.loads(df.to_json()) for name, df in data.items()}
        return jsonobjects, 200
    else:
        series1 = retrieve_data(datasource, experimentId1, measurements, fields, match_series, remove_outliers, additional_clause, chunked, chunk_size, limit, offset, max_lag)
        if series1 is None:
            return {"error": f"Data source {datasource} is currently not available."}, 404
        series1.index = series1.index - series1.index.min()
        series2 = retrieve_data(datasource, experimentId2, measurements, fields, match_series, remove_outliers, additional_clause, chunked, chunk_size, limit, offset, max_lag)
        series2.index = series2.index - series2.index.min()
        series_dict = synchronize(dataframes={'series1': series1, 'series2': series2}, max_lag=max_lag, merge=False)
        for series_name, series in series_dict.items():
            series_dict[series_name] = json.loads(series.to_json())
        return series_dict, 200


def get_secrets():
    try:
        with open("/run/secrets/analytics_connections", 'r') as secret_file:
            return secret_file.read().strip()
    except IOError:
        return None


if __name__ == '__main__':
    # Get login details from secret
    secrets = get_secrets()
    sources = {}

    if secrets:
        connections = yaml.safe_load(secrets)

        # Establish database connections

        for con_name, con_details in connections.items():
            for database in con_details["databases"]:
                sources[con_name + '_' + database] = DataCollector(con_details["host"], con_details["port"], con_details["user"], con_details["password"], database)

    # Data cache
    data_cache = {}
    enable_cache = environ.get("ENABLE_CACHE", "False").lower() == "true"

    # Start app
    app.run(host='0.0.0.0', port=5000, debug=False)
