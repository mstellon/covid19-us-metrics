import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import requests
import plotly.express as px

from plot_config import config

def build_table(data, id=None, drop=None):
    """expects dict"""
    if drop:
        data = {k:v for k,v in data.items() if k not in drop}
    header = [html.Thead(html.Tr([html.Td(k) for k in data.keys()]))]
    body = [html.Tbody(html.Tr([html.Td(f"{v or 0:,}") for v in data.values()]))]
    return dbc.Table(header + body, bordered=True, responsive=True, id=id)


def national_stats(data, update):
    return dbc.Col([
        html.H3("United States National Stats"),
        html.P(html.Small(f"Last update: {update}")),
        build_table(data)
    ])

def grade_card(grade):
    if grade == 'A':
        color = 'success'
    elif grade in ('B','C','D'):
        color = 'warning'
    else:
        color = 'danger'
    card = html.H5(["Reporting Grade ", dbc.Badge(grade,color=color)], style={"text-align":"right"})
    return card

def state_info(state, data):
    if not state:
        return ""

    state_info, state_current = data.get_state_data(state)
    state_grade = data.get_state_grade(state)
    net_new_graph=px.bar(data.state_net_new(state), x='date',y='new')
    net_new_graph.update_layout(title='Net New Cases', xaxis_tickformat='%b-%d', yaxis_tickformat=',', xaxis_title='Date', yaxis_title='')

    return [dbc.Col(dcc.Graph(id='state_new', figure=net_new_graph,  config=config),lg=6),
                dbc.Col(dbc.Card([
                    dbc.CardHeader(dbc.Row([
                                    dbc.Col(html.H3(state_info['name'])), 
                                    dbc.Col(grade_card(state_grade), align='center')
                                    ], justify='between')
                                    ),
                    dbc.CardBody([dbc.Row(
                        dbc.Col(build_table(state_current, id='state-data'))
                        ),
                        dbc.Row([
                            dbc.Col("place holders",lg=4),
                            dbc.Col([
                                dcc.Markdown(state_info.get('notes', ""))
                            ])
            
                        ])
                        ])
            ]),lg=6)]
