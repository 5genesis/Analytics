__author__ = 'Erik Aumayr, SRL'

from flask import Flask, send_file
import plotly
import plotly.graph_objects as go
import dash
import dash_table
from dash_table.Format import Format, Scheme
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import numpy as np
from dash.dependencies import Input, Output, State
import json
import requests
from urllib.parse import urlparse, parse_qs
import pandas as pd
from datetime import datetime
from io import BytesIO
import jwt
from typing import List, Tuple


class Crypt:

    def __init__(self, secret: str):
        self.secret = secret

    def Encode(self, target: int, executions: List[int]) -> str:
        """'target' is the landing experiment execution, 'executions' is
        the list of all executions belonging to the user"""
        payload = {"t": target, "l": executions}
        token = jwt.encode(payload, self.secret, algorithm="HS256")
        if isinstance(token, bytes):  # Older versions of jwt return bytes
            token = token.decode(encoding="UTF-8")
        return token

    def Decode(self, token: str) -> Tuple[int, List[int]]:
        """Returns a tuple (<landing execution>, <list of executions>)"""
        payload = jwt.decode(token, self.secret, algorithms=["HS256"])
        return payload["t"], payload["l"]


server = Flask(__name__)


@server.route('/', methods=['GET'])
def index():
    return {'about': "Visualization service for 5Genesis Analytics Component. Visit /help for more info and /dash to bring up the dashboard."}, 200


# Fetch the data source options
def fetch_datasource_options():
    link = "http://data_handler:5000/get_datasources"
    try:
        data = requests.get(link).json()
        return [{'label': item, 'value': item} for item in data['sources']]
    except requests.HTTPError:
        return [{'label': 'No datasource available', 'value': ''}]


datasource_options = fetch_datasource_options()

app = dash.Dash(
    __name__,
    server=server,
    routes_pathname_prefix='/dash/',
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

stat_indicators = ['Mean', 'Standard Deviation', 'Median', 'Min', 'Max',
                   '25% Percentile', '75% Percentile', '5% Percentile', '95% Percentile']

app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Img(src=app.get_asset_url('5genesis_logo.png'),  # from https://pbs.twimg.com/media/EWm7hjlX0AUl_AJ.png
                         style={'height': '12rem', 'width': '12rem', 'border-radius': '50%'}),
                html.H2("Analytics", style={'margin-top': '2rem'})
            ], style={'display': 'block', 'text-align': 'center', 'padding-top': '2rem'}),
            html.Br(),
            html.Div([
                html.Div('Database'),
                dcc.Dropdown(
                    options=datasource_options,
                    value=datasource_options[0]['value'],
                    id='datasource',
                    searchable=False,
                    clearable=False
                )
            ]),
            html.Br(),
            html.Div([
                html.Div('Experiment ID'),
                dcc.Dropdown(id='experiment')
            ]),
            html.Br(),
            html.Div([
                html.Div('Measurement Table'),
                dcc.Dropdown(
                    id='measurement',
                    multi=True)
            ]),
            html.Br(),
            html.Div([
                html.Div('Available Features'),
                dcc.Dropdown(id='kpi', multi=True)
            ]),
            html.Br(),
            html.Hr(),
            html.Br(),
            html.Div([
                html.Div('Outlier Detection Algorithm'),
                dcc.Dropdown(
                    options=[
                        {'label': 'None', 'value': 'None'},
                        {'label': 'Z-score', 'value': 'zscore'},
                        {'label': 'MAD', 'value': 'mad'}],
                    value='None',
                    id='outlier',
                    searchable=False,
                    clearable=False
                )]),
            html.Br(),
            html.Div([
                html.Div('Time resolution'),
                dcc.Input(
                    id="time_resolution",
                    type='text',
                    placeholder="1s",
                    value='1s',
                    style={'width': '75px'}
                )
            ]),
            html.Br(),
            html.Div(
                html.A(
                    dbc.Button('Reset', id='purge_cache_button'),
                    href='/dash/'
                ), style={'textAlign': 'center'})
        ], width=2, style={'background-color': "#f8f9fa"}),
        dbc.Col([
            # Hidden divisions to store data that'll be used as input for different callbacks
            html.Div(id='df', style={'display': 'none'}),
            html.Div(id='df_no_outliers', style={'display': 'none'}),

            html.Div(id='test_case_stat_df', style={'display': 'none'}),
            html.Div(id='it_stat_df', style={'display': 'none'}),

            # html.Div(id='corr_matrix_download_data', style={'display': 'none'}),
            # html.Div(id='corr_table_download_data', style={'display': 'none'}),

            html.Div(id='prediction_results_df', style={'display': 'none'}),

            # html.Br(),

            # Create tabs
            dcc.Tabs(id='tabs', value='time-series-tab', children=[

                # Time Series tab
                dcc.Tab(label='Time Series Overview', value='time-series-tab', children=[
                    # Time series graph
                    dbc.Row(dbc.Col(dcc.Graph(id='graph'))),
                    # dcc.Graph(id='graph_no_outliers')

                    # # download link
                    # dbc.Row(dbc.Col(
                    #     html.A(
                    #         'Download Raw Data',
                    #         id='download-link',
                    #         download="",
                    #         href="",
                    #         target="_blank"
                    #     )
                    # ))
                ]),

                # Statistical Analysis tab
                dcc.Tab(label='Statistical Analysis', value='stat-analysis-tab', children=[
                    # graph
                    dbc.Row(dbc.Col(
                        dcc.Graph(id='box_plot')
                    )),

                    # table
                    dbc.Row(dbc.Col([
                        html.H4(children='Test Case Statistics'),
                        dash_table.DataTable(
                            id='table',
                            columns=[
                                {'name': 'Indicator', 'id': 'Indicator'},
                                {'name': 'Value', 'id': 'Value', 'type': 'numeric',
                                    'format': Format(precision=2, scheme=Scheme.fixed)},
                                {'name': 'Confidence Interval', 'id': 'Confidence Interval', 'type': 'numeric',
                                    'format': Format(precision=2, scheme=Scheme.fixed)}
                            ]
                        ),
                        # # download links
                        # html.Div(
                        #     html.A(
                        #         'Download Per Iteration Statistics',
                        #         id='iteration_download',
                        #         download="",
                        #         href="",
                        #         target="_blank"
                        #     ),
                        # ),
                        # html.Div(
                        #     html.A(
                        #         'Download Test Case Statistics',
                        #         id='test_case_download',
                        #         download="",
                        #         href="",
                        #         target="_blank"
                        #     )
                        # )
                    ], width=6), justify='center')
                ]),

                # Correlation tab
                dcc.Tab(label='Correlation', value='correlation-tab', children=[
                    dcc.Tabs(id="corr-tabs", value="cross-correlation-tab", children=[
                        # Correlation Matrix
                        dcc.Tab(label='Cross-correlation of fields within the same experiment', value="cross-correlation-tab", children=[
                            dbc.Row(dbc.Col([
                                html.Div('Correlation method', style={'margin-top': '20px'}),
                                dcc.Dropdown(
                                    options=[
                                        {'value': 'pearson', 'label': 'Pearson correlation coefficient'},
                                        {'value': 'kendall', 'label': 'Kendall Tau correlation coefficient'},
                                        {'value': 'spearman', 'label': 'Spearman rank correlation'}
                                    ],
                                    value='pearson',
                                    id='correlation-method',
                                    searchable=False,
                                    clearable=False
                                )
                            ], width=3)),
                            dbc.Row(dbc.Col(
                                dcc.Graph(id='correlation_graph')
                            )),
                            # dbc.Row(dbc.Col(
                            #     # download link
                            #     html.A(
                            #         'Download Correlation Matrix Data',
                            #         id='corr_matrix_download',
                            #         download="",
                            #         href="",
                            #         target="_blank"
                            #     )
                            # ))
                        ]),

                        # Correlation table
                        dcc.Tab(label='Correlation of fields between two different experiments', value='experiment-correlation-tab', children=[
                            dbc.Row(dbc.Col([
                                html.Div('Pick Second Experiment ID', style={'margin-top': '20px'}),
                                dcc.Dropdown(id='experiment2'),
                                html.Br()
                            ], width=3), justify='center'),
                            dbc.Row(dbc.Col(
                                dash_table.DataTable(
                                    id='correlation_table',
                                    columns=[
                                        {'name': 'Correlation Field', 'id': 'Correlation Field', 'type': 'text'},
                                        {'name': 'Value', 'id': 'Value', 'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed)}
                                    ], style_data={'width': '250px'}
                                ), width='auto'
                            ), justify='center'),
                            # dbc.Row(dbc.Col(
                            #     # download link
                            #     html.A(
                            #         'Download Correlation Table Data',
                            #         id='corr_table_download',
                            #         download="",
                            #         href="",
                            #         target="_blank"
                            #     )
                            # ))
                        ])
                    ])
                ]),

                # Feature Selection tab
                dcc.Tab(label='Feature Selection', value='feature-selection-tab', children=[
                    # hidden division to store data
                    html.Div(id='feature_score', style={'display': 'none'}),
                    dbc.Row([
                        dbc.Col([
                            # Options
                            html.Div('Select Algorithm', style={'margin-top': '20px'}),
                            dcc.Dropdown(
                                options=[
                                    {'label': 'Backward Elimination', 'value': 'backward'},
                                    {'label': 'RFE', 'value': 'rfe'},
                                    {'label': 'Lasso', 'value': 'lasso'}
                                ],
                                value='lasso',
                                id='method',
                                searchable=False,
                                clearable=False
                            )
                        ], width=2),
                        dbc.Col([
                            html.Div('Drop Features', style={'margin-top': '20px'}),
                            dcc.Dropdown(
                                id='drop_features',
                                multi=True
                            )
                        ], width=3),
                        dbc.Col([
                            html.Div('Normalize (for RFE)', style={'margin-top': '20px'}),
                            dcc.RadioItems(
                                options=[
                                    {'label': 'Yes', 'value': 'true'},
                                    {'label': 'No', 'value': 'false'},
                                ],
                                value='true',
                                id='normalize',
                                labelStyle={'display': 'inline-block', 'margin-top': '5px'}
                            )
                        ], width='auto'),
                        dbc.Col([
                            html.Div('Alpha (for Lasso)', style={'margin-top': '20px'}),
                            dcc.Input(
                                id='alpha',
                                type='number',
                                value=0.1,
                                min=0, max=10, step=0.1
                            )
                        ], width='auto')
                    ]),
                    dbc.Row(dbc.Col(dcc.Graph(id='feature_bar'))),
                    # dbc.Row(dbc.Col(
                    #     # download link
                    #     html.A(
                    #         'Download Feature Selection Scores',
                    #         id='features_download',
                    #         download="",
                    #         href="",
                    #         target="_blank"
                    #     )
                    # ))
                ]),

                # Prediction tab
                dcc.Tab(label='Prediction', value='prediction-tab', children=[
                    dbc.Row([
                        # Options
                        dbc.Col([
                            html.Div('Select Algorithm', style={'margin-top': '20px'}),
                            dcc.Dropdown(
                                options=[
                                    {'label': 'Linear Regression',
                                        'value': 'linreg'},
                                    {'label': 'Random Forest',
                                        'value': 'rf'},
                                    {'label': 'SVR', 'value': 'svr'}
                                ],
                                value='linreg',
                                id='algorithm',
                                searchable=False,
                                clearable=False
                            )
                        ], width=2),
                        dbc.Col([
                            html.Div('Drop Features', style={'margin-top': '20px'}),
                            dcc.Dropdown(
                                id='drop_features_pred',
                                multi=True
                            )
                        ], width=3),
                        dbc.Col(
                            dbc.Button('Automatic feature selection', id='drop_features_button', color='light', style={'margin-top': '43px'}),
                            width="auto"
                        ),
                        dbc.Col(
                            dbc.Button('Train model', id='train_button', style={'margin-top': '43px'}),
                            width="auto"
                        )
                    ]),
                    dbc.Row(
                        # Prediction values graph
                        dbc.Col(dbc.Col(dcc.Graph(id='predicted_values_graph')))
                    ),
                    dbc.Row([
                        # Prediction results
                        dbc.Col(
                            html.Div([
                                html.H4('Training results'),
                                dash_table.DataTable(
                                    id='prediction_result_table',
                                    columns=[
                                        {
                                            'name': 'Metric',
                                            'id': 'Metric',
                                            'type': 'text'
                                        }, {
                                            'name': 'Value',
                                            'id': 'Value',
                                            'type': 'numeric',
                                            'format': Format(precision=2, scheme=Scheme.fixed)
                                        }
                                    ]
                                )
                            ], style={'text-align': 'center'}), width=4
                        ),

                        # Coefficient table
                        dbc.Col(
                            html.Div([
                                html.H4('Model coefficients'),
                                dash_table.DataTable(
                                    id='prediction_coefficient_table',
                                    columns=[
                                        {
                                            'name': 'Feature',
                                            'id': 'Feature',
                                            'type': 'text'
                                        }, {
                                            'name': 'Value',
                                            'id': 'Value',
                                            'type': 'numeric',
                                            'format': Format(precision=4, scheme=Scheme.fixed)
                                        }
                                    ]
                                )
                            ], style={'text-align': 'center'}), width=4
                        )
                    ], justify="around"),
                    dbc.Row(
                        dbc.Col(
                            html.A(
                                dbc.Button('Download model', id='download_button', style={'margin-bottom': '50px'}),
                                id='model_download_link',
                                href=None
                            ), width="auto"
                        ), justify="center"
                    )
                ])
            ])
        ])
    ])
], fluid=True)


def empty_figure(title='No data'):
    return {
        'data': [{'x': 0, 'y': 0}],
        'layout': {'title': title}
    }


empty_fig = empty_figure()

kpi_filter_list = ['Available RAM', 'PacketsReceived', 'Total RAM', 'Used CPU Per Cent', 'Used RAM', 'Used RAM Per Cent',  # malaga old names
                   'host', 'Cell ID', 'Cell',
                   'facility', 'facility_x', 'facility_y',
                   'Success', 'Success_x', 'Success_y',
                   'hostname', 'hostname_x', 'hostname_y',
                   'appname', 'appname_x', 'appname_y',
                   'series', 'series_x', 'series_y',
                   '_iteration_', '_iteration__x', '_iteration__y',
                   'ExecutionId', 'ExecutionId_x', 'ExecutionId_y', 'Timestamp_x', 'Timestamp_y',
                   'Operator', 'DateTime', 'Network', 'LAC', 'PSC',
                   'AWGN State', 'Verdict']

meas_filter_list = ['execution_metadata', 'syslog']


# callback to return experiment ID options
@app.callback(
    [Output('experiment', 'options'),
     Output('experiment', 'value')],
    [Input('url', 'search'),
     Input('datasource', 'value')])
def experimentID_list(search, datasource):
    if not search or not datasource:
        return [], None
    start = datetime.now()
    params = parse_qs(urlparse(search).query)
    token = params['token'][0]
    if token == secret:
        link = f'http://data_handler:5000/get_all_experimentIds/{datasource}'
        r = requests.get(link)
        experiment_list = list(r.json().values())[0]
        experiment_target = None
    else:
        experiment_target, experiment_list = decoder.Decode(token)
    if experiment_target and experiment_target not in experiment_list:
        experiment_list += [experiment_target]
    print(f"-- experimentID_list: {datetime.now()-start}", flush=True)
    return [{'label': item, 'value': item} for item in sorted(experiment_list)], experiment_target


# callback to return measurement options
@app.callback(
    [Output('measurement', 'options'),
     Output('measurement', 'value')],
    [Input('experiment', 'value')],
    [State('datasource', 'value')])
def find_measurement(experiment, datasource):
    if not experiment or not datasource:
        return [], None
    start = datetime.now()

    link = f'http://data_handler:5000/get_measurements_for_experimentId/{datasource}/{experiment}'
    r = requests.get(link)
    meas_list = list(r.json().values())[0]
    temp = []
    for i in meas_list:
        if i not in meas_filter_list:  # to avoid having measurement tables which raise errors
            temp.append({'label': i, 'value': i})
    print(f"-- find_measurement: {datetime.now()-start}", flush=True)
    return temp, None

# callback used to store the df in a hidden division


@app.callback(
    Output('df', 'children'),
    [Input('measurement', 'value'),
     Input('outlier', 'value'),
     Input('datasource', 'value'),
     Input('experiment', 'value'),
     Input('time_resolution', 'value'),
     Input('purge_cache_button', 'n_clicks')])
def retrieve_df(measurement, outlier, datasource, experiment, time_resolution, purge_cache):
    # input check - this order required (at first value is none, when filled it is a list)
    if not measurement or not experiment or not time_resolution:
        # empty_df = pd.DataFrame(data={})
        return None
    context = dash.callback_context
    if context and context.triggered[0]['prop_id'].split('.')[0] == 'purge_cache_button':
        requests.get('http://data_handler:5000/purge_cache')
        return None

    start = datetime.now()
    link = f'http://data_handler:5000/get_data/{datasource}/{experiment}'
    param_dict = {
        'match_series': False,
        'measurement': measurement,
        'max_lag': time_resolution,
        'remove_outliers': outlier
    }
    r = requests.get(link, params=param_dict)
    print(f"-- retrieve_df: {datetime.now()-start}", flush=True)
    # return df.to_json()
    return r.text


@app.callback(
    [Output('kpi', 'options'),
     Output('kpi', 'value')],
    [Input("df", "children")])
def update_dropdown(df):
    if not df:
        return [], None
    start = datetime.now()
    temp = []
    df = pd.read_json(df)
    for i in df.columns:
        if not len(df[i].dropna()) == 0 and i not in kpi_filter_list:
            temp.append({'label': i, 'value': i})
    print(f"-- update_dropdown: {datetime.now()-start}", flush=True)
    return temp, None


###
# Time Series Overview tab
###

# Time series graph
@app.callback(
    Output('graph', 'figure'),
    [Input('kpi', 'value'),
     Input("outlier", 'value'),
     Input('tabs', 'value')],
    [State("df", "children")])
def update_graph(kpi, outlier, tab, df):

    # input check
    if not kpi or not df or not outlier or tab != "time-series-tab":
        return empty_fig
    start = datetime.now()
    df = pd.read_json(df)
    traces = []
    for i in range(len(kpi)):
        feature = kpi[i]
        series = df[feature]
        series.reset_index(drop=True, inplace=True)
        traces.append(go.Scatter(
            x=df.index,
            y=series,
            mode='lines',
            name=feature,
            yaxis=f"y{i+1}" if i > 0 else 'y'
        ))

    figure = {
        'data': traces,
        'layout': {
            'title': 'Time Series',
            'xaxis': {
                'title': 'Samples',
                'domain': [0, 1 - (len(kpi) - 1) * 0.06],
                'titlefont': {
                    'family': 'Helvetica, monospace',
                    'size': 20,
                    'color': '#7f7f7f'
                }
            },
            'yaxis': {
                'title': kpi[0],
                'titlefont': {
                    'family': 'Helvetica, monospace',
                    'size': 20,
                    'color': plotly.colors.DEFAULT_PLOTLY_COLORS[0]
                },
                'tickfont': {
                    'color': plotly.colors.DEFAULT_PLOTLY_COLORS[0]
                }
            },
            "showlegend": False
        }
    }
    for i in range(1, len(kpi)):
        figure['layout'][f'yaxis{i+1}'] = {
            'title': kpi[i],
            'titlefont': {
                'family': 'Helvetica, monospace',
                'size': 20,
                'color': plotly.colors.DEFAULT_PLOTLY_COLORS[i]
            },
            'tickfont': {
                'color': plotly.colors.DEFAULT_PLOTLY_COLORS[i]
            },
            'overlaying': 'y',
            'side': 'right',
            'position': 1 - i * 0.06
        }

    print(f"-- update_graph: {datetime.now()-start}", flush=True)
    return figure


###
# Statistical Analysis tab
###

# callback used to store the statistical analysis dataframes
@app.callback(
    [Output("it_stat_df", "children"),
     Output("test_case_stat_df", "children")],
    [Input('kpi', 'value'),
     Input('datasource', 'value'),
     Input('tabs', 'value')],
    [State('measurement', 'value'),
     State('experiment', 'value')])
def retrieve_stats(kpi, datasource, tab, measurement, experiment):
    if not kpi or not experiment or tab != 'stat-analysis-tab':
        empty_df = pd.DataFrame(data={})
        return empty_df.to_json(), empty_df.to_json()
    else:
        link = f'http://statistical_analysis:5003/statistical_analysis/{datasource}'
        param_dict = {
            'experimentid': experiment,
            'kpi': kpi[0],  # .replace(" ","%20")
            'measurement': measurement
        }
        r = requests.get(link, params=param_dict)
        data = r.json()
        if not data['experimentid'][experiment]:
            return pd.DataFrame().to_json(), pd.DataFrame().to_json()
        temp = data['experimentid'][experiment][kpi[0]]
        df1 = pd.DataFrame.from_dict(temp['Iteration Statistics'], orient='index').reset_index()
        test_case_stat_df = pd.DataFrame.from_dict(temp['Test Case Statistics'], orient='index').reset_index()
        df1.rename(columns={'index': 'Iteration'}, inplace=True)
        test_case_stat_df.rename(columns={'index': 'Indicator'}, inplace=True)
        return df1.to_json(), test_case_stat_df.to_json()


# return box plot
@app.callback(
    Output('box_plot', 'figure'),
    [Input('kpi', 'value'),
     Input("tabs", "value")],
    [State("df", "children")])
def update_box_plot_graph(kpi, tab, df):
    if not kpi or not df or tab != 'stat-analysis-tab':
        return empty_fig
    else:
        kpi = kpi[0]
        df = pd.read_json(df)
        it_list = None
        if '_iteration_' in df:
            it_list = df._iteration_.unique()
        if it_list is None or len(it_list) < 2:
            return empty_figure(title='<b style="color:red">Warning: No iteration recorded in the data!</b>')
        N = len(df._iteration_.unique()) + 1
        c = ['hsl(' + str(h) + ',50%' + ',50%)' for h in np.linspace(0, 360, N)]
        trace = []
        for it in range(len(it_list)):
            temp = df[df._iteration_ == it]
            trace.append(go.Box(y=temp[kpi], name=f'{it}', marker_color=c[it]))

        figure = {

            'data': trace,

            'layout': {
                'title': 'Per-Iteration Statistics',
                'xaxis': dict(
                    title='Iteration',
                    tickmode='array',
                    tickvals=list(range(N)),
                    titlefont=dict(
                        family='Helvetica, monospace',
                        size=20,
                        color='#7f7f7f'
                    )),
                'yaxis': dict(
                    title=kpi,
                    titlefont=dict(
                        family='Helvetica, monospace',
                        size=20,
                        color='#7f7f7f'
                    )),
                "showlegend": False
            }
        }
    return figure


# return test case statistics table
@app.callback(
    Output('table', 'data'),
    [Input('test_case_stat_df', 'children'),
     Input("tabs", "value")])
def update_table(test_case_stat_df, tab):
    if not test_case_stat_df or len(test_case_stat_df) == 2 or tab != 'stat-analysis-tab':
        return [{'Indicator': None, 'Value': None, 'Confidence Interval': None}]
    else:
        df = pd.read_json(test_case_stat_df)
        return df.to_dict('records')


# # callback used to return the download link for the raw data
# @app.callback([
#     Output('download-link', 'href'),
#     Output('download-link', 'download')],
#     [Input('df', 'children'),
#      Input('datasource', 'value'),
#      Input("tabs", "value")],
#     [State('measurement', 'value'),
#      State('experiment', 'value')])
# def update_download_link_raw(df, datasource, tab, measurement, experiment):
#     if not df or len(df) == 2 or tab != 'stat-analysis-tab':
#         csv_string = None
#         download_string = None
#     else:
#         dff = pd.read_json(df)
#         csv_string = dff.to_csv(index=False, encoding='utf-8')
#         csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
#         download_string = f'raw_{datasource}_{experiment}_{measurement}.csv'

#     return csv_string, download_string


# # callbacks to return download links for statistical analysis
# @app.callback([
#     Output('iteration_download', 'href'),
#     Output('iteration_download', 'download')],
#     [Input('it_stat_df', 'children'),
#      Input('kpi', 'value'),
#      Input('datasource', 'value'),
#      Input("tabs", "value")],
#     [State('measurement', 'value'),
#      State('experiment', 'value')])
# def update_download_link_stat_data(it_stat_df, kpi, datasource, tab, measurement, experiment):
#     if not it_stat_df or len(it_stat_df) == 2 or tab != 'stat-analysis-tab':
#         csv_string = None
#         download_string = None
#     else:
#         dff = pd.read_json(it_stat_df)
#         csv_string = dff.to_csv(index=False, encoding='utf-8')
#         csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
#         download_string = f'per_it_stats_{datasource}_{experiment}_{measurement}_{kpi}.csv'

#     return csv_string, download_string


# # callbacks to return download links for test case
# @app.callback([
#     Output('test_case_download', 'href'),
#     Output('test_case_download', 'download')],
#     [Input('test_case_stat_df', 'children'),
#      Input('kpi', 'value'),
#      Input('datasource', 'value'),
#      Input("tabs", "value")],
#     [State('measurement', 'value'),
#      State('experiment', 'value')])
# def update_download_link_test_case(test_case_stat_df, kpi, datasource, tab, measurement, experiment):
#     if not test_case_stat_df or tab != 'stat-analysis-tab':
#         csv_string = None
#         download_string = None
#     else:
#         dff = pd.read_json(test_case_stat_df)
#         csv_string = dff.to_csv(index=False, encoding='utf-8')
#         csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
#         download_string = f'test_case_stats_{datasource}_{experiment}_{measurement}_{kpi}.csv'

#     return csv_string, download_string


###
# Correlation tab
###

###
# Field Correlation sub tab
###

# correlation matrix callback
@app.callback(
    Output('correlation_graph', 'figure'),
    #  Output('corr_matrix_download_data', 'children'),
    [Input('outlier', 'value'),
     Input('measurement', 'value'),
     Input("tabs", "value"),
     Input("corr-tabs", "value"),
     Input('kpi', 'value'),
     Input('correlation-method', 'value')],
    [State('experiment', 'value'),
     State('datasource', 'value')])
def correlation_matrix(outlier, measurement, tab, corr_tab, kpis, correlation_method, experiment, datasource):
    if not measurement or not outlier or tab != "correlation-tab" or corr_tab != "cross-correlation-tab":
        return empty_fig
    start = datetime.now()
    link = f'http://correlation:5001/correlate/fields/{datasource}/{experiment}'
    param_dict = {
        'measurement': measurement,
        'field': kpis,
        'remove_outliers': outlier,
        'method': correlation_method
    }
    r = requests.get(link, params=param_dict)
    data = r.json()

    df = pd.DataFrame(data['correlation_matrix']).select_dtypes(exclude=object).dropna(how='all')
    x = df.columns
    y = df.index[::-1]
    z = df.values[::-1]

    figure = {
        'data': [
            {
                'type': 'heatmap',
                'x': x,
                'y': y,
                'z': z,
                'zmin': -1,
                'zmax': 1,
                'colorscale': [[0, 'red'], [0.5, 'white'], [1.0, 'green']]
            }
        ],
        'layout': {
            'title': '<b>Correlation Matrix</b><br>Mouseover to read the exact data (x and y labels with corresponding correlation weight).',
            'margin': {'l': 250, 'r': 250, 'b': 120},  # margin to avoid label cut - hardcoded because 'auto' doesn't work
            'height': max(450, 20 * len(x))
        },
        'frames': []
    }
    # download_data = pd.DataFrame(temp).to_json()
    print(f"-- correlation_matrix: {datetime.now()-start}", flush=True)
    return figure
    # return figure, download_data


# # download link for correlation matrix data
# @app.callback(
#     [Output('corr_matrix_download', 'href'),
#      Output('corr_matrix_download', 'download')],
#     [Input('corr_matrix_download_data', 'children'),
#      Input("tabs", "value"),
#      Input("corr-tabs", "value")],
#     [State('datasource', 'value'),
#      State('measurement', 'value'),
#      State('outlier', 'value'),
#      State('experiment', 'value'),
#      ])
# def update_download_link_correlation(corr_matrix_download_data, tab, corr_tab, datasource, measurement, outlier, experiment):
#     if not corr_matrix_download_data or tab != "correlation-tab" or corr_tab != "cross-correlation-tab":
#         csv_string = None
#         download_string = None
#     else:
#         df_temp1 = pd.read_json(corr_matrix_download_data)

#         df_temp2 = df_temp1.dropna(how='all')  # drop rows where all elements are empty
#         df = df_temp2.dropna(axis=1, how='all')  # drop columns where all elements are empty

#         csv_string = df.to_csv(index=True, encoding='utf-8')
#         csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
#         download_string = f'correlation_matrix_data_{datasource}_{experiment}_{measurement}_{outlier}.csv'

#     return csv_string, download_string


###
# Cross experiment correlation sub tab
###

# callback to return experiment2 ID options
@app.callback(
    Output('experiment2', 'options'),
    [Input('experiment', 'value'),
     Input('experiment', 'options'),
     Input("corr-tabs", "value")],
    [State("tabs", "value")])
def find_second_experimentID(experiment, experiments, corr_tab, tab):
    if experiment and experiments and tab == "correlation-tab" and corr_tab == "experiment-correlation-tab":
        return experiments
    else:
        return []


# return correlation table
@app.callback(
    Output('correlation_table', 'data'),
    #  Output('corr_table_download_data', 'children')],
    [Input('outlier', 'value'),
     Input('experiment', 'value'),
     Input('experiment2', 'value'),
     Input('measurement', 'value'),
     Input('kpi', 'value'),
     Input('datasource', 'value'),
     Input("tabs", "value"),
     Input("corr-tabs", "value")],
    [State('correlation-method', 'value')])
def update_experiment_correlation_table(outlier, experiment, experiment2, measurement, kpis, datasource, tab, corr_tab, correlation_method):
    if not experiment2 or not measurement or tab != "correlation-tab" or corr_tab != "experiment-correlation-tab":
        correlation_list = []
        # download_data = None
    else:
        if measurement is not None:
            link = f'http://correlation:5001/correlate/experiments/{datasource}/{experiment}/{experiment2}'
            param_dict = {
                'measurement': measurement,
                'field': kpis,
                'remove_outliers': outlier,
                'method': correlation_method
            }
            r = requests.get(link, params=param_dict)
            if r.status_code != 200:
                return []
            data = r.json()
            temp = data['correlation_list']

            correlation_list = []
            for k, v in temp.items():
                if not pd.isna(v):
                    correlation_list.append({'Correlation Field': k, 'Value': v})
        # download_data = pd.DataFrame(correlation_list).to_json()

    return correlation_list
    # return correlation_list, download_data


# # download link for correlation table data
# @app.callback(
#     [Output('corr_table_download', 'href'),
#      Output('corr_table_download', 'download')],
#     [Input('corr_table_download_data', 'children'),
#      Input('datasource', 'value'),
#      Input('measurement', 'value'),
#      Input('outlier', 'value'),
#      Input('experiment', 'value'),
#      Input('experiment2', 'value'),
#      Input('kpi', 'value'),
#      Input("tabs", "value"),
#      Input("corr-tabs", "value")])
# def update_download_link_experiment_correlation(corr_table_download_data, datasource, measurement, outlier, experiment, experiment2, kpi, tab, corr_tab):
#     if not corr_table_download_data or tab != "correlation-tab" or corr_tab != "experiment-correlation-tab":
#         csv_string = None
#         download_string = None
#     else:
#         df_temp = pd.read_json(corr_table_download_data)
#         df = df_temp.reset_index(drop=True)  # sets rows in increasing order

#         csv_string = df.to_csv(index=True, encoding='utf-8')
#         csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
#         download_string = f'correlation_table_data_{datasource}_{experiment}_{experiment2}_{measurement}_{kpi}_{outlier}.csv'

#     return csv_string, download_string


###
# Feature Selection tab
###

# Drop feature dropdown list
@app.callback(
    Output('drop_features', 'options'),
    [Input('kpi', 'value'),
     Input("tabs", "value")],
    [State('df', 'children')])
def update_drop_features(kpi, tab, df):
    # input check
    if not df or not kpi or tab != "feature-selection-tab":  # len(df) <= 0 or kpi == None:
        return []
    start = datetime.now()
    df = pd.read_json(df).select_dtypes(exclude=object).dropna(how='all', axis=1)
    print(f"-- update_table: {datetime.now()-start}", flush=True)
    return [{'label': i, 'value': i} for i in df.drop(kpi, 1).columns]


# return bar plot of features importance
@app.callback([
    Output('feature_bar', 'figure'),
    Output('feature_score', 'children')],
    [Input('kpi', 'value'),
     Input("tabs", "value"),
     Input("outlier", 'value'),
     Input('method', 'value'),
     Input("drop_features", "value"),
     Input('normalize', 'value'),
     Input('alpha', 'value')],
    [State('datasource', 'value'),
     State('measurement', 'value'),
     State('experiment', 'value')])
def update_featureselection_graph(kpi, tab, outlier, method, drop_features, normalize, alpha, datasource, measurement, experiment):

    if not kpi or not experiment or not measurement or not alpha or tab != "feature-selection-tab":
        return empty_fig, None
    start = datetime.now()
    kpi = kpi[0]
    kpi = kpi.replace(" ", "%20")
    link = f'http://feature_selection:5004/selection/{datasource}/{method}/{kpi}'
    param_dict = {
        'experimentid': experiment,
        'remove_outliers': outlier,
        'alpha': alpha,
        'normalize': normalize,
        'drop_feature': drop_features,
        'measurement': measurement
    }
    r = requests.get(link, params=param_dict)
    data = r.json()['Score']
    df = pd.DataFrame.from_dict(data, orient='index')

    if sum(df[0]) == 0:
        title = "<b>Feature selection cannot be performed on this feature since it is constant over time.</b><br>Running the same analysis with no outlier detection (set to 'None') may solve this issue for some of the features in the dataset."
    else:
        title = "Score"

    figure = {
        'data': [go.Bar(
            y=list(data.values()),
            x=list(data.keys())
        )],
        'layout': {
            'title': title,
            'xaxis': dict(
                title='Features',
                tickangle=30,
                tickfont=dict(family='Rockwell', size=10),
                titlefont=dict(
                    family='Helvetica, monospace',
                    size=16,
                    color='#7f7f7f'
                ))
        }
    }
    print(f"-- update_featureselection_graph: {datetime.now()-start}", flush=True)
    return figure, df.to_json()


# # callback which returns download link for feature scores
# @app.callback([
#     Output('features_download', 'href'),
#     Output('features_download', 'download')],
#     [Input('feature_score', 'children'),
#      Input('kpi', 'value'),
#      Input('method', 'value'),
#      Input("tabs", "value")],
#     [State('datasource', 'value'),
#      State('measurement', 'value'),
#      State('experiment', 'value')])
# def update_download_link(feature_score, kpi, method, tab, datasource, measurement, experiment):
#     if not feature_score or len(feature_score) == 2 or tab != "feature-selection-tab":
#         csv_string = None
#         download_string = None
#     else:
#         dff = pd.read_json(feature_score)
#         csv_string = dff.to_csv(index=True, encoding='utf-8')
#         csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
#         download_string = f'test_case_stats_{datasource}_{experiment}_{measurement}_{kpi}_{method}.csv'
#     return csv_string, download_string


###
# Prediction tab
###


# Train button, which saves the model training results in a hidden Div
@app.callback(
    [Output("prediction_results_df", "children"),
     Output('model_download_link', 'href')],
    [Input("train_button", 'n_clicks')],
    [State('datasource', 'value'),
     State('algorithm', 'value'),
     State('kpi', 'value'),
     State('experiment', 'value'),
     State('drop_features_pred', 'value'),
     State('drop_features_pred', 'options'),
     State('measurement', 'value'),
     State("outlier", "value"),
     State('time_resolution', 'value'),
     State("tabs", "value")])
def train_model(train_button, datasource, algorithm, target, experimentid, drop_features, drop_features_available, measurements, remove_outliers, time_resolution, tab):
    if not datasource or not algorithm or not target or not experimentid or not measurements or tab != "prediction-tab":
        return None, None
    if drop_features and len(drop_features_available) == len(drop_features):  # This happens when all features are selected for dropping and none remain
        return None, None

    target = target[0].replace(' ', '%20')
    start = datetime.now()
    param_dict = {
        'experimentid': experimentid,
        'drop_feature': drop_features,
        'measurement': measurements,
        'remove_outliers': remove_outliers,
        'max_lag': time_resolution
    }
    r = requests.get(f'http://prediction:5002/train/{datasource}/{algorithm}/{target}', params=param_dict)
    results = r.json()

    print(f"-- train_model: {datetime.now()-start}", flush=True)
    return json.dumps(results), f"/prediction/model/{algorithm}"


# Populate drop feature dropdown list
@app.callback(
    Output('drop_features_pred', 'options'),
    [Input('kpi', 'value'),
     Input("tabs", "value")],
    [State('df', 'children')])
def update_drop_features_prediction(kpi, tab, df):
    if not df or not kpi or tab != "prediction-tab":
        return []
    start = datetime.now()
    df = pd.read_json(df).select_dtypes(exclude=object).dropna(how='all', axis=1)
    print(f"-- update_table: {datetime.now()-start}", flush=True)
    return [{'label': i, 'value': i} for i in df.drop(kpi, 1).columns]


# Run feature selection for the prediction by pressing the drop feature button
@app.callback(
    Output('drop_features_pred', 'value'),
    [Input('drop_features_button', 'n_clicks')],
    [State('datasource', 'value'),
     State('method', 'value'),
     State('kpi', 'value'),
     State('experiment', 'value'),
     State('outlier', 'value'),
     State('alpha', 'value'),
     State('normalize', 'value'),
     State('measurement', 'value'),
     State('drop_features_pred', 'options')])
def select_features_for_prediction(drop_features_button, datasource, method, kpi, experiment, outlier, alpha, normalize, measurements, all_features):
    if not datasource or not kpi or not experiment or not measurements or not all_features:
        return None
    kpi = kpi[0]  # .replace(' ', '%20')
    all_features = [item['value'] for item in all_features]
    selected_features = []
    link = f'http://feature_selection:5004/selection/{datasource}/{method}/{kpi}'
    param_dict = {
        'experimentid': experiment,
        'remove_outliers': outlier,
        'alpha': alpha,
        'normalize': normalize,
        'measurement': measurements
    }
    r = requests.get(link, params=param_dict)
    data = r.json()
    selected_features = data['Features - Selected']
    return [item for item in all_features if item not in selected_features]


# Results table
@app.callback(
    Output('prediction_result_table', 'data'),
    [Input("prediction_results_df", "children")],
    [State("tabs", "value")])
def update_prediction_results_table(prediction_results_df, tab):
    if not prediction_results_df or tab != 'prediction-tab':
        return [{'Metric': None, 'Value': None}]
    else:
        results = json.loads(prediction_results_df)
        return [{'Metric': k, 'Value': v} for k, v in results['results'].items() if k in [
            'Cross-val R2 score (mean)',
            'Cross-val explained_variance score (mean)',
            'Explained variance score',
            'Mean Absolute Error',
            'Mean Squared Error',
            'Prediction mean',
            'Prediction std',
            'R2 score',
            'Test mean',
            'Test std',
            'Train mean',
            'Train std']]


# Actual vs predicted graph
@app.callback(
    Output('predicted_values_graph', 'figure'),
    [Input("prediction_results_df", "children")],
    [State("tabs", "value"),
     State('kpi', 'value')])
def update_prediction_graph(prediction_results_df, tab, kpi):
    if not prediction_results_df or tab != 'prediction-tab':
        return empty_fig

    start = datetime.now()
    results = json.loads(prediction_results_df)
    figure = {

        'data': [go.Scatter(x=[float(item) for item in results['real_predicted_values']['y_test'].values()],
                            y=[float(item) for item in results['real_predicted_values']['y_pred'].values()],
                            name=kpi[0],
                            mode='markers')],

        'layout': {
            'title': f'Predicted vs actual values for {kpi[0]}',
            'xaxis': dict(
                title='Actual',
                titlefont=dict(
                    family='Helvetica, monospace',
                    size=20,
                    color='#7f7f7f'
                )),
            'yaxis': dict(
                title='Predicted',
                titlefont=dict(
                    family='Helvetica, monospace',
                    size=20,
                    color='#7f7f7f'
                ))
        }
    }
    print(f"-- update_prediction_graph: {datetime.now()-start}", flush=True)
    return figure


# Coefficients table
@app.callback(
    Output('prediction_coefficient_table', 'data'),
    [Input("prediction_results_df", "children")],
    [State("tabs", "value")])
def update_prediction_coefficients_table(prediction_results_df, tab):
    if not prediction_results_df or tab != 'prediction-tab':
        return [{'Feature': None, 'Value': None}]
    else:
        results = json.loads(prediction_results_df)
        return [{'Feature': k, 'Value': v} for k, v in results['coefficients'].items()]


@app.server.route('/prediction/model/<string:algorithm>')
def download_model(algorithm):
    model = requests.get('http://prediction:5002/model').content
    return send_file(
        BytesIO(model),
        mimetype='application/octet-stream',
        as_attachment=True,
        attachment_filename=algorithm + '.pickle'
    )


def get_secret():
    try:
        with open("/run/secrets/analytics_secret", 'r') as secret_file:
            return secret_file.read().strip()
    except IOError:
        return None


if __name__ == '__main__':
    secret = get_secret()
    decoder = Crypt(secret=secret)
    app.run_server(host='0.0.0.0', port=5005, debug=False)
