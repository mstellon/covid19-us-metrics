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

def state_map(data):

    fig = px.choropleth(data_frame=data, locations='state',locationmode='USA-states', 
                    scope='usa',
                    color='value',
                   color_continuous_scale='reds',
                   width=1000,
                   title='Total Confirmed Positives')
    fig.update_layout(title_x=.5, margin_r=0, margin_l=0, margin_autoexpand=True, showlegend=False, coloraxis_showscale=False)
    return dcc.Graph(id='map',figure=fig, config=config)

def national_stats(data, update):
    return dbc.Col([
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
    card = html.H5(["Reporting Grade ", dbc.Badge(grade,color=color)], style={"text-align":"right"})
    return card

def line_graph(data):
    fig = px.line(data, x='date',y='value', color='variable')
    fig.update_layout(title=None, xaxis_tickformat='%b-%d', yaxis_tickformat=',', 
    xaxis_title='Date', yaxis_title='', legend_title=None, legend_orientation='h',
    margin_autoexpand=True, margin_l=0, margin_r=0, margin_t=0)
    return fig

def state_info(state, data):
    if not state:
        return ""

    state_info, state_current = data.get_state_data(state)
    state_grade = data.get_state_grade(state)
    fig = line_graph(data.state_net_new(state))

    return [dbc.Col(dcc.Graph(id='state_new', figure=fig,  config=config),lg=6),
                dbc.Col(dbc.Card([
                    dbc.CardHeader(dbc.Row([
                                    dbc.Col(html.H3(state_info['name'])), 
                                    dbc.Col(grade_card(state_grade), align='center')
                                    ], justify='between')
                                    ),
                    dbc.CardBody([dbc.Row(
                        dbc.Col([
                            html.H5("Current Totals"),
                            build_table(state_current, id='state-data')]
                            )
                        ),
                        dbc.Row([
                            dbc.Col("place holders",lg=4),
                            dbc.Col([
                                dcc.Markdown(state_info.get('notes', ""))
                            ])
            
                        ])
                        ])
            ]),lg=6)]
