from io import BytesIO
from datetime import datetime
import pytz
import os
import time

import requests
import requests_cache
import pandas as pd
import numpy as np
import us
import zipfile

root = os.path.dirname(__file__)

requests_cache.install_cache(expire_after=900, backend='memory')
STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

DATA_TTL = 1800
class Data(object):
    def __init__(self):
        self.url = 'https://covidtracking.com/api'
        self.col_rename = {
                'positive':'Confirmed Positive',
                'positivepercap':"Positive Per 10K",
                'negative':'Reported Negative',
                'hospitalized': 'Reported Hospitalized',
                'death': 'Deaths',
                'testspercap': "Tests per 10K"
                #'totalTestResults':'Total Reported Tests'
                }
        self.graph_rename = {"positiveIncrease": "Positives per Day",
                            "totalTestResultsIncrease": "Tests per Day",
                            "deathIncrease": "Deaths per Day",
                            'deaths_mean':"Projected Deaths per Day",
                            'admis_mean':"Projected Hospital Admission per Day",
                            'allbed_mean':"Projected Total Hospital Beds Needed per Day"}
        self.graph_tab_mapping = [
            ["positiveIncrease"],
            ["deathIncrease","deaths_mean"],
            ["admis_mean","allbed_mean"]
        ]
        self.pop_df = pd.read_csv(os.path.join(root,'data/census_pop.csv'))

        self.last_update_time = None
        self.daily_state_df = self.setup_state_data()

        

    def setup_state_data(self):
        # only update if TTL is exceeded
        if self.last_update_time:
            if time.time() - self.last_update_time > DATA_TTL:
                return self.daily_state_df



        df = pd.read_json(self.url + '/states/daily')
        df['date'] = pd.to_datetime(df['date'],format='%Y%m%d')
        df = df.merge(self.pop_df,on='state',how='inner')
        df['positivepercap'] = df['positive'] / (df['population'] / 10000)
        df['testspercap'] = df['totalTestResults'] / (df['population'] / 10000)
        self.last_update_time = time.time()
        return df
    
    def get_projections(self):
        url = "https://ihmecovid19storage.blob.core.windows.net/latest/ihme-covid19.zip"
        resp = requests.get(url)
        
        f = BytesIO(resp.content)
        z = zipfile.ZipFile(f)
        csvf = [f for f in z.namelist() if ".csv" in f]
        csv = BytesIO(z.read(csvf[0]))
        df = pd.read_csv(csv)
        df['state'] = df.location.map(self.get_state)
        df['date'] = pd.to_datetime(df['date'],format='%Y-%m-%d')
        # keep future projections
        df = df[df['date'] >= pd.to_datetime('today')]
        return df[['date','state','deaths_mean', 'admis_mean','allbed_mean']]

    def get_state(self, x):
        state = us.states.lookup(x,field='name')
        if state:
            return state.abbr
        else:
            return x
    @property
    def states(self):
        return sorted(self.daily_state_df['state'].unique().tolist())

    @property
    def state_dropdown(self):
        return [{"label":s,"value":s } for s in STATES]


    def top_by_cap(self, n=5):
        df = self.current_by_state()
        df.sort_values('positivepercap', ascending=False, inplace=True)
        df = df[:n]
        df['#'] = range(1,n + 1)
        return df[['#','state','positivepercap', 'testspercap']].round({"positivepercap":2, "testspercap":2})\
                .rename(columns={"state":"State","positivepercap":"Positive per 10K People", "testspercap":"Tests per 10K People"})\
                .to_dict(orient='records')
    def current_by_state(self):
        # refresh data - since this is cached it is not a big peformance issue
        self.daily_state_df = self.setup_state_data()

        df = self.daily_state_df
        df = df.sort_values(['state','date']).drop_duplicates('state',keep='last')
        
        return df

    
    def get_state_graph_data(self, state, cols=None):
        if not cols:
            cols = ['positiveIncrease','deathIncrease','totalTestResultsIncrease',
                    'deaths_mean', 'admis_mean','allbed_mean']
        df = self.daily_state_df.query(f"state=='{state}'")
        proj = self.get_projections().query(f"state=='{state}'")
        df = df.merge(proj, on=['date','state'], how='outer')
        df = df.melt(id_vars=['date','state'],value_vars=cols)
        df['variable'] = df['variable'].map(self.graph_rename)
        return df

    def get_national_stats(self):
        us = requests.get(self.url + '/us').json()[0]
        
        us['positivepercap'] = round(us['positive'] / 33036.2592,2) #us 10k pop
        us['testspercap'] = round(us['totalTestResults'] / 33036.2592,2)

        us_data = {}
        for k,v in self.col_rename.items():
            us_data[v] = us[k]
    
        return us_data

    def get_national_historic(self, cols=None):
        if not cols:
            cols = ['positiveIncrease','deathIncrease','totalTestResultsIncrease',
                    'deaths_mean', 'admis_mean','allbed_mean']
        #cols.append('date')
        df = pd.read_json(self.url + '/us/daily')
        df['date'] = pd.to_datetime(df['date'],format='%Y%m%d')
        proj = self.get_projections().query("state=='US'")
        df = df.merge(proj, on=['date'], how='outer')
        df = df.melt(id_vars=['date'],value_vars=cols)
        df['variable'] = df['variable'].map(self.graph_rename)

        return df

    @property
    def national_last_update(self):
        resp = requests.get(self.url + '/us')
        last_mod = resp.json()[0]['lastModified']
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
        state_pop = self.pop_df.query(f"state=='{state}'")['population'].values[0]

        state_current['positivepercap'] = round(state_current['positive'] / (state_pop/10000),2) #us 10k pop
        state_current['testspercap'] = round(state_current['totalTestResults'] / (state_pop/10000),2)
        state_current = {v: state_current[k] for k,v in self.col_rename.items()}
        return state_info, state_current
