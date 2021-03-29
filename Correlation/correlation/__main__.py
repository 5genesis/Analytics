__author__ = 'Erik Aumayr'

from flask import Flask, request
import json
import requests
import pandas as pd
from correlation.correlation import correlate_fields, correlate_experiments

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return {'about': "Correlation service for 5Genesis Analytics Component. Visit /help for more info."}, 200


@app.route('/help')
@app.route('/API')
@app.route('/api')
def get_help():
    response = {
        "/correlate/fields/datasource/experimentId": {
            "default parameters": {
                'method': "pearson (any Pandas correlation method)",
                'measurement': "None (individual measurement name, e.g. Throughput_Measures)",
                'remove_outliers': "None (zscore or mad)",
                'field': 'List of selected fields (default None, i.e. all fields selected)'
            },
            "datasource": "uma"
        },
        "/correlate/experiments/datasource/experimentId1/experimentId2": {
            "default parameters": {
                'method': "pearson (any Pandas correlation method)",
                'measurement': "None (individual measurement name, e.g. Throughput_Measures)",
                'remove_outliers': "None (zscore or mad)",
                'fields': 'List of selected fields (default None, i.e. all fields selected)'
            },
            "datasource": "uma, athens_iperf, athens_rtt"
        }
    }
    return response, 200


@app.route('/correlate/fields/<string:datasource>/<string:experimentId>', methods=['GET'])
def get_correlate_fields(datasource, experimentId):
    method = request.args.get('method', 'pearson')
    measurements = request.args.getlist('measurement')
    remove_outliers = request.args.get('remove_outliers')  # zscore, mad or None
    fields = request.args.getlist('field')
    link = f'http://data_handler:5000/get_data/{datasource}/{experimentId}'
    param_dict = {
        'field': fields,
        'match_series': False,
        'remove_outliers': remove_outliers,
        'measurement': measurements
    }
    r = requests.get(link, params=param_dict)
    data = r.json()
    df = pd.DataFrame(data)
    correlations = correlate_fields(df, method=method)
    results = {k: json.loads(v.to_json()) for k, v in correlations.items()}
    return {"correlation_matrix": results}, 200


@app.route('/correlate/experiments/<string:datasource>/<string:experimentId1>/<string:experimentId2>', methods=['GET'])
def get_correlate_experiments(datasource, experimentId1, experimentId2):
    method = request.args.get('method', 'pearson')
    measurements = request.args.getlist('measurement')
    remove_outliers = request.args.get('remove_outliers')  # zscore, mad or None
    fields = request.args.getlist('field')
    link = f'http://data_handler:5000/get_data/{datasource}/{experimentId1}/{experimentId2}'
    param_dict = {
        'field': fields,
        'remove_outliers': remove_outliers,
        'measurement': measurements
    }
    r = requests.get(link, params=param_dict)
    data = r.json()
    series = {}
    for s_name, s in data.items():
        series[s_name] = pd.DataFrame(s)
    return {"correlation_list": json.loads(correlate_experiments(series, method=method).to_json())}, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
