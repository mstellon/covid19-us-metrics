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
        
        self.daily_state_df = self.setup_state_data()

    def setup_state_data(self):
        df = pd.read_json(self.url + '/states/daily')
        # get current data and append
        current = pd.read_json(self.url + '/states')
        max_dt = max(df['dateChecked'])
        current = current[current['dateModified']>max_dt]
        current['date'] = current['dateModified']\
        .map(lambda x: x.split('T')[0].replace('-',''))

        df = df.sort_values(['state','dateChecked'])\
                .drop_duplicates(['state','dateChecked'],keep='last')

        df.sort_values(['state','date'], ascending=False, inplace=True)

        df['new'] = np.where(df['state'] != df['state'].shift(-1), 
                                0,df['positive'] - df['positive'].shift(-1))

        return df

    @property
    def states(self):
        return sorted(self.daily_state_df['state'].unique().tolist())

    @property
    def state_dropdown(self):
        return [{"label":s,"value":s } for s in STATES]

    @property
    def current_by_state(self):
        return self.daily_state_df.sort_values(['state','date']).drop_duplicates('state',keep='last')
    
    def state_net_new(self, state):
        df = self.daily_state_df.query(f"state=='{state}'")
        return df

    def get_national_stats(self):
        us = requests.get(self.url + '/us').json()[0]
        
        rename = {
                'positive':'Confirmed Positive',
                'negative':'Reported Negative',
                'hospitalized': 'Reported Hospitalized',
                'death': 'Deaths',
                'totalTestResults':'Total Reported Tests'
                }


        us_data = {}
        for k,v in rename.items():
            us_data[v] = us[k]
    
        return us_data
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
        rename = {
                'positive':'Confirmed Positive',
                'negative':'Reported Negative',
                'hospitalized': 'Reported Hospitalized',
                'death': 'Deaths',
                'totalTestResults':'Total Reported Tests',
                }
        state_current = {v: state_current[k] for k,v in rename.items()}
        return state_info, state_current
