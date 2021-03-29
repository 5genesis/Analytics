from flask import Flask, request
import json
import urllib
import pandas as pd
from statistical_analysis.statistical_analysis import KPI_statistics



app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return {'about': "Statistical Analysis service for 5Genesis Analytics Component. Visit /help for more info."}, 200


@app.route('/help')
@app.route('/API')
@app.route('/api')
def get_help():
    response = {
        "/statistical_analysis": {
            "default parameters": {
                'experimentid': "None",
                'measurement': "None (individual measurement table in InfluxDB, e.g. Throughput_Measures)",
                'it': "_iteration_ (iteration identifier)",
                'kpi': "None (kpi to analyze)",
                'unit': "None (e.g. ms, Mbps)",
                'exptype' : {'0': 'if the experiments contain several kpi samples per iteration (default)', '1': 'if the experiments contain one kpi sample per iteration (e.g. Service Creation Time)'}
            }
        }
    }
    return response, 200

@app.route("/statistical_analysis/<string:datasource>")
def stat(datasource):

    experimentIds = request.args.getlist('experimentid')
    measurements = request.args.getlist('measurement')
    measurements = ("&measurement="+"&measurement=".join(measurements)) if measurements else ""
    it = request.args.get('it')

    if not it:
        it='_iteration_'

    kpis = request.args.getlist('kpi')

    unit = request.args.getlist('unit')

    if unit:
        kpi2unit=dict(zip(kpis,unit))
    else:
        kpi2unit={}

    exp_type = request.args.get('exptype')

    if (not exp_type or exp_type!=1):
        exp_type=0

    final_diz={}
    name1='Iteration Statistics'
    name2='Test Case Statistics'

    for experimentid in experimentIds:
        with urllib.request.urlopen(f'http://data_handler:5000/get_data/{datasource}/{experimentid}?match_series=false{measurements}') as response:

            data = json.loads(response.read())

        diz={}

        # for s_name, s in data.items():

        series=pd.DataFrame(data)

        diz1={}
        diz2={}

        for kpi in kpis:

            kpi_name=f'{kpi} - ({kpi2unit[kpi]})' if kpi in kpi2unit else kpi

            try:

                temp1,temp2=KPI_statistics(series,it,kpi,exp_type)
                diz1[name1]=temp1.to_dict('index')
                diz2[name2]=temp2.to_dict('index')
                diz[kpi_name]={**diz1,**diz2}

            except:

                continue

        final_diz[experimentid]=diz

    return {'experimentid': json.loads(json.dumps(final_diz))}, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=False)
