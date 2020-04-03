from datetime import datetime
import pytz

import requests
import requests_cache
import pandas as pd
import numpy as np

requests_cache.install_cache(expire_after=900, backend='memory')
STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
class Data(object):
    def __init__(self):
        self.url = 'https://covidtracking.com/api'
        
        self.col_rename = {
                'positive':'Confirmed Positive',
                'negative':'Reported Negative',
                'hospitalized': 'Reported Hospitalized',
                'death': 'Deaths',
                'totalTestResults':'Total Reported Tests'
                }
        self.graph_rename = {"positiveIncrease": "Positives per Day",
                            "totalTestResultsIncrease": "Tests per Day",
                            "deathIncrease": "Deaths per Day"}

        self.daily_state_df = self.setup_state_data()

    def setup_state_data(self):
        df = pd.read_json(self.url + '/states/daily')
        df['date'] = pd.to_datetime(df['date'],format='%Y%m%d')
        return df

    @property
    def states(self):
        return sorted(self.daily_state_df['state'].unique().tolist())

    @property
    def state_dropdown(self):
        return [{"label":s,"value":s } for s in STATES]

    def current_by_state(self):
        df = self.daily_state_df
        return df.sort_values(['state','date']).drop_duplicates('state',keep='last')
    
    def get_state_graph_data(self, state, cols=None):
        if not cols:
            cols = ['positiveIncrease','deathIncrease','totalTestResultsIncrease']
        cols.append('date')
        cols.append('state')
        df = self.daily_state_df.query(f"state=='{state}'")

        return df[cols]

    def get_national_stats(self):
        us = requests.get(self.url + '/us').json()[0]

        us_data = {}
        for k,v in self.col_rename.items():
            us_data[v] = us[k]
    
        return us_data

    def get_national_historic(self, cols=None):
        if not cols:
            cols = ['positiveIncrease','deathIncrease','totalTestResultsIncrease']
        cols.append('date')
        df = pd.read_json(self.url + '/us/daily')
        df['date'] = pd.to_datetime(df['date'],format='%Y%m%d')
        df = df[cols]
        #df = df.melt(id_vars=['date'],value_vars=cols)

        return df

    @property
    def national_last_update(self):
        last_mod = requests.get(self.url + '/us').json()[0]['lastModified']
        eastern = pytz.timezone('US/Eastern')
        dt = datetime.strptime(last_mod, '%Y-%m-%dT%H:%M:%S.%f%z')
        dt = dt.astimezone(eastern)
        return dt.strftime('%A, %B %d, %Y %I:%M%p %Z %zUTC')

    def get_state_grade(self, state):
        data =  requests.get(self.url + '/states', params={'state':state}).json()
        return data['grade']
    def get_state_data(self, state):
        state_info = requests.get(self.url + '/states/info', params={"state":state}).json()
        state_current = requests.get(self.url + '/states', params={'state':state}).json()
        state_current = {v: state_current[k] for k,v in self.col_rename.items()}
        return state_info, state_current
