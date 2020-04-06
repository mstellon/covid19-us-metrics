import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import requests
import plotly.express as px
from plotly import graph_objects as go

from plot_config import config


def build_table(data, id=None, drop=None):
    """expects dict"""
    if drop:
        data = {k:v for k,v in data.items() if k not in drop}
    header = [html.Thead(html.Tr([html.Td(k) for k in data.keys()]))]
    body = [html.Tbody(html.Tr([html.Td(f"{v or 0:,}") for v in data.values()]))]
    return dbc.Table(header + body, bordered=True, responsive=True, id=id)

def state_map(data):

    fig = px.choropleth(data_frame=data, locations='state',locationmode='USA-states', 
                    scope='usa',
                    color='positivepercap',
                   color_continuous_scale='reds',
                   width=1000,
                   title='Total Confirmed Positives per 10,000')
    fig.update_layout(title_x=.5, margin_r=0, margin_l=0, margin_autoexpand=True, showlegend=False, coloraxis_showscale=False)
    return dcc.Graph(id='map',figure=fig, config=config)

def national_stats(data, update):
    return html.Div([
        html.H3("United States National Stats"),
        html.P(html.Small(f"Last update: {update}")),
        html.H4("Current Totals"),
        build_table(data)
    ])

def grade_card(grade):
    if grade == 'A':
        color = 'success'
    elif grade in ('B','C','D'):
        color = 'warning'
    else:
        color = 'danger'
    card = html.H5([html.A("Reporting Grade",href="https://covidtracking.com/about-data#data-quality-grade", target="_blank"),
                    " ",
                    dbc.Badge(grade,color=color)], style={"text-align":"right"})
    return card

def build_checkboxes(data, id):
    """Expects dict with where value is the label
    of the checkbox
    """

    ops = [{"label": v, "value":k} for k,v in data.items()]
    return  dbc.Col(dbc.Checklist(
            options= ops,
            value=list(data.keys()),
            id=id,
            switch=True,
            inline=True
        ))


def line_graph(data):
    fig = px.line(data, x='date',y='value', color='variable', height=500)
    fig.update_layout(title=None, xaxis_tickformat='%b-%d', yaxis_tickformat=',', 
    xaxis_title='Date', yaxis_title='', 
    showlegend=True,
    legend_title=None, legend_orientation='h', legend_itemclick='toggle',
    legend_x=0.5, legend_xanchor='center', legend_borderwidth=1, legend_y=1.15,
    margin_autoexpand=True, margin_t=10, autosize=True
    )

    return dcc.Graph(figure=fig, config=config)

def graph_tabs(id):
    tabs =dbc.Col([
        dbc.Tabs(
        [
            dbc.Tab(label="Confirmed Positives per Day", tab_id=f"{id}-0"),
            dbc.Tab(label="Deaths per Day", tab_id=f"{id}-1"),
            dbc.Tab(label="Other Projections", tab_id=f"{id}-2")

        ],id=f"{id}-tabs",
         active_tab=f"tab{id}-0"
        ),
        html.Div(id=id)
    ]
    )
    return tabs


def state_list_per_cap(data):
    """Expects list of dicts"""
    body = []
    header = [html.Thead(html.Tr([html.Td(k) for k in data[0].keys()]))]
    for d in data:
        body.append(html.Tr([html.Td(v) for v in d.values()]))
    
    return dbc.Table(header + [html.Tbody(body)], bordered=True, responsive=True)

def state_info(state, data):
    if not state:
        return dbc.Col("")

    state_info, state_current = data.get_state_data(state)
    state_grade = data.get_state_grade(state)
    last_update = data.state_last_update(state)

    return [dbc.Col([
                graph_tabs(id="state-graph") 
                ]),
                dbc.Col(dbc.Card([
                    dbc.CardHeader(dbc.Row([
                                    dbc.Col(html.H3(state_info['name'])), 
                                    dbc.Col(grade_card(state_grade), align='center')
                                    ], justify='between')
                                    ),
                    dbc.CardBody([dbc.Row(
                        dbc.Col([
                            html.H5("Current Totals"),
                            html.Small(f"Last updated - {last_update}"),
                            build_table(state_current, id='state-data')]
                            )
                        ),
                        dbc.Row([
                            dbc.Col([html.H5("State Links"),
                                    dbc.ListGroup([
                                        dbc.ListGroupItem("Covid Site",href=state_info['covid19Site'], target="_blank"),
                                        dbc.ListGroupItem("Secondary Covid Site", href=state_info['covid19SiteSecondary'], target="_blank"),
                                        dbc.ListGroupItem("Twitter", href=f"https://twitter.com/{state_info['twitter']}", target="_blank")

                                    ])
                                    
                            
                            ],width=4),
                            dbc.Col([
                                html.H5("Data notes"),
                                dcc.Markdown(state_info.get('notes', ""))
                            ])
            
                        ])
                        ])
            ]))]
