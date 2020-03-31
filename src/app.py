# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_html_components as html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc



import pandas as pd
import plotly.express as px
import requests

import components
from data import Data
from plot_config import config
data = Data()

external_stylesheets = [{"src":"https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css",
 "integrity":"sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh",
 "crossorigin":"anonymous"},
   
   
   #"https://unpkg.com/material-components-web@v4.0.0/dist/material-components-web.min.css",
#'https://codepen.io/chriddyp/pen/bWLwgP.css'
]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
      dbc.Row(components.national_stats(data.get_national_stats(), data.national_last_update)),
      dbc.Row(
      dcc.Graph(id='map',figure=px.choropleth(data_frame=data.current_by_state, locations='state',locationmode='USA-states', 
                    scope='usa',
                    color='positive',
                   color_continuous_scale='reds',
                   width=1000,
                   
      ), config=config)),
      dbc.Row([
          dbc.Col([
          html.H3("State Level detail"),
          html.Small("Click on map above or use drop-down")
          ]),
          dbc.Col(dcc.Dropdown(id='state-dropdown', options=data.state_dropdown,
          placeholder='Select a State'))
      ]
      ),
      dbc.Row(id='state')
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
def map_state_dropdown(input_value):
    if input_value:
        return components.state_info(input_value,data)
    else:
        return ""
    

  
if __name__ == '__main__':
    app.run_server(debug=True, port=5000, host='0.0.0.0')
