from flask import Flask, request
import json
import urllib
import pandas as pd
from feature_selection.RFE import RFE_selector
from feature_selection.backward_elimination import backward_elimination
from feature_selection.LASSO import LASSO


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return {'about': "Feature selection service for 5Genesis Analytics Component. Visit /help for more info."}, 200


@app.route('/help')
@app.route('/API')
@app.route('/api')
def get_help():
    response = {
        "/selection/datasource/algorithm/target": {
            "algorithm": "backward_elimination, rfe, lasso",
            "default parameters": {
                'experimentid': "None (at least one experiment ID is mandatory)",
                'measurement': "None (individual measurement name, e.g. Throughput_Measures)",
                'drop_feature': "None (any feature to be ignored for training)",
                'remove_outliers': "None (zscore or mad)",
                'normalize': "False (or True, relevant just for RFE)",
                'alpha': "0.1 (constant that multiplies the L1 term in Lasso)"
            },
            "datasource": "uma, athens_iperf, athens_rtt"
        }
    }
    return response, 200


@app.route("/selection/<string:datasource>/<string:algorithm>/<string:target>")
def selection(datasource, algorithm, target):

    experimentIds = request.args.getlist('experimentid')
    measurements = request.args.getlist('measurement')
    measurements = ("&measurement="+"&measurement=".join(measurements)) if measurements else ""
    drop_features = request.args.getlist('drop_feature')
    alpha=request.args.get('alpha')
    if not alpha:
        alpha=.1
    alpha=float(alpha)

    remove_outliers = request.args.get('remove_outliers')
    normalize = request.args.get('normalize')

    series = pd.DataFrame()
    for experimentId in experimentIds:
        with urllib.request.urlopen(f'http://data_handler:5000/get_data/{datasource}/{experimentId}?match_series=false&remove_outliers={remove_outliers}{measurements}') as response:
            data = json.loads(response.read())
        series = series.append(pd.DataFrame(data).reset_index(drop=True))
        # series = series.append(pd.DataFrame(data['series']))

    if algorithm in ['backward', 'backward_elimination']:
        new_features, original_features,score = backward_elimination(series, target=target, drop_features=drop_features)

    elif algorithm in ['rfe', 'RFE']:
        new_features, original_features, score = RFE_selector(series, target=target, drop_features=drop_features,normalize=normalize)

    elif algorithm in ['lasso', 'Lasso','LASSO']:
        new_features, original_features, score = LASSO(series, target=target, alpha=alpha,drop_features=drop_features)

    return {'Features - Selected': new_features, 'Features - Original': original_features, 'Score': json.loads(score.to_json(orient='index'))},200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=False)
