import os

import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_html_components as html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import flask
from flask_caching import Cache

import pandas as pd
import plotly.express as px
import requests

import components
from data import Data
from plot_config import config
root = os.path.dirname(__file__)
with open(os.path.join(root,'intro.md'),'r') as f:
    intro = f.read()

data = Data()

external_stylesheets = [{"src":"https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css",
 "integrity":"sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh",
 "crossorigin":"anonymous"},
   
   
   #"https://unpkg.com/material-components-web@v4.0.0/dist/material-components-web.min.css",
#'https://codepen.io/chriddyp/pen/bWLwgP.css'
]

server = flask.Flask(__name__)

app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'COVID-19 US Metrics'
cache = Cache(app.server, config={
    'CACHE_TYPE': 'simple',
})
CACHE_TTL = 1800
app.config.suppress_callback_exceptions = True

app.layout = dbc.Container([
      dbc.Row([dbc.Col([
          dbc.Row(
              [dbc.Col(html.H1("Covid-19 Metrics")),
              dbc.Col(html.A("Github",href="https://github.com/mstellon/covid19-us-metrics", target="_blank"), style={"text-align":"right"})
              
              ]
              ,justify='between'),
          
          html.Hr(),
          dcc.Markdown(intro)

      ])]),
      dbc.Row(dbc.Col([components.national_stats(data.get_national_stats(), data.national_last_update)])),
      dbc.Row([
          dbc.Col([
             html.H3("Past and Projected Data"),
              html.P("Click legend to turn data elements on or off"),
              html.Div(components.graph_tabs(id="national-graph"))
          ]),
          
          ]),
      dbc.Row([
          dbc.Col([html.H5("Top States"),
          components.state_list_per_cap(data.top_by_cap(10))], width=4),
          dbc.Col(components.state_map(data.current_by_state()), width=8)
          
          ]),
      dbc.Row(dbc.Col(html.Hr())),
      dbc.Row([
          dbc.Col([
          html.H3("State Level detail"),
          html.Small("Click on map above or use drop-down")
          ]),
          dbc.Col(dcc.Dropdown(id='state-dropdown', options=data.state_dropdown,
          placeholder='Select a State'))
      ]
      ),
      dbc.Row(id='state'),
      dbc.Row(dbc.Col(html.Hr())),
      
      ])

@app.callback(
    Output(component_id='state-dropdown', component_property='value'),
    [Input(component_id='map', component_property='clickData')]
)
def map_click(input_value):
    try:
        state = input_value['points'][0]['location']
    except TypeError:
        raise PreventUpdate
    return state

@app.callback(
Output(component_id='state',component_property='children'),
[Input(component_id='state-dropdown', component_property='value')]
)
@cache.memoize(timeout=CACHE_TTL) 
def map_state_dropdown(input_value):
    if input_value:
        return components.state_info(input_value,data)
    else:
        return dbc.Col("")

@app.callback(
    Output(component_id='national-graph', component_property="children"),
    [Input(component_id='national-graph-tabs',component_property="active_tab")]
)
@cache.memoize(timeout=CACHE_TTL) 
def tab_change(at):

    idx = int(at[-1])

    cols = data.graph_tab_mapping[idx]

    return components.line_graph(data.get_national_historic(cols=cols))
@app.callback(
    Output(component_id='state-graph', component_property="children"),
    [Input(component_id='state-graph-tabs',component_property="active_tab"),
    Input(component_id='state-dropdown', component_property='value')]
)
@cache.memoize(timeout=CACHE_TTL) 
def state_tab_change(at, state):
    if at:
        idx = int(at[-1])
    else:
        idx = 0
    cols = data.graph_tab_mapping[idx]
    return components.line_graph(data.get_state_graph_data(state,cols=cols))

  
if __name__ == '__main__':
    app.run_server(debug=True, port=5000, host='0.0.0.0')
