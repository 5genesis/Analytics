__author__ = 'Erik Aumayr'

from flask import Flask, request, send_file
import json
import requests
import pandas as pd
from prediction.regression import linear_regression
from prediction.random_forest import random_forest
from prediction.SVR import svr, linear_svr, nu_svr
import pickle
from io import BytesIO


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return {'about': "Prediction service for 5Genesis Analytics Component. Visit /help for more info."}, 200


@app.route('/help')
@app.route('/API')
@app.route('/api')
def get_help():
    response = {
        "/predict/datasource/algorithm/target": {
            "algorithm": "linreg, rf, svr, linear_svr, nu_svr",
            "default parameters": {
                'experimentid': "None (at least one experiment ID is mandatory)",
                'measurement': "None (individual measurement name, e.g. Throughput_Measures)",
                'drop_feature': "None (any feature to be ignored for training)",
                'remove_outliers': "None (zscore or mad)",
                'normalize': "False (or True, not relevant for some algorithms, e.g. Random Forest or SVR)"
            },
            "datasource": "uma, athens_iperf, athens_rtt"
        },
        "/download_model": "Pickled Scikit-Learn model"
    }
    return response, 200


@app.route("/model")
def download_model():
    if not last_trained_model:
        return {"warning": "No trained model available."}, 200
    pickled_model_string = pickle.dumps(last_trained_model[1])
    return send_file(
        BytesIO(pickled_model_string),
        mimetype='application/octet-stream',
        as_attachment=True,
        attachment_filename=last_trained_model[0] + '.pickle'
    ), 200


@app.route("/train/<string:datasource>/<string:algorithm>/<string:target>")
def predict(datasource, algorithm, target):
    global last_trained_model
    last_trained_model = None
    experimentIds = request.args.getlist('experimentid')
    if not experimentIds or experimentIds == []:
        return {"error": "Must specify at least one experimentId with experimentid=123."}, 400
    measurements = request.args.getlist('measurement')
    drop_features = request.args.getlist('drop_feature')
    remove_outliers = request.args.get('remove_outliers')
    normalize = request.args.get('normalize')
    normalize = normalize.lower() == 'true' if normalize else False
    max_lag = request.args.get('max_lag', '1s')
    coefficients = None
    results = None
    y_values = None
    series = pd.DataFrame()
    for experimentId in experimentIds:
        param_dict = {
            'measurement': measurements,
            'drop_feature': drop_features,
            'remove_outliers': remove_outliers,
            'normalize': normalize,
            'max_lag': max_lag
        }
        r = requests.get(f'http://data_handler:5000/get_data/{datasource}/{experimentId}', params=param_dict)
        data = r.json()
        series = series.append(pd.DataFrame(data).reset_index(drop=True))
    if algorithm in ['linreg', 'linear_regression']:
        coefficients, results, y_values, model = linear_regression(
            series, target=target, drop_features=drop_features, split=0.2, normalize=normalize)
        last_trained_model = ['Linear Regression', model]
    elif algorithm in ['rf', 'random_forest']:
        coefficients, results, y_values, model = random_forest(
            series, target=target, drop_features=drop_features, split=0.2)
        last_trained_model = ['Random Forest', model]
    elif algorithm in ['svr']:
        coefficients, results, y_values, model = svr(
            series, kernel='linear', target=target, drop_features=drop_features, split=0.2)
        last_trained_model = ['Support Vector Regression', model]
    elif algorithm in ['linear_svr']:
        coefficients, results, y_values, model = linear_svr(
            series, target=target, drop_features=drop_features, split=0.2)
        last_trained_model = ['Linear SVR', model]
    elif algorithm in ['nu_svr']:
        coefficients, results, y_values, model = nu_svr(
            series, kernel='linear', target=target, drop_features=drop_features, split=0.2)
        last_trained_model = ['Nu SVR', model]
    return {'coefficients': json.loads(coefficients.to_json()), 'results': json.loads(results.to_json()), 'real_predicted_values': json.loads(y_values.to_json())}, 200


if __name__ == '__main__':
    last_trained_model = None
    app.run(host='0.0.0.0', port=5002, debug=False)
