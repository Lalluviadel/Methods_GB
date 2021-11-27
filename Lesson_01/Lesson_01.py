import json
from datetime import datetime, timedelta
from pprint import pprint

import requests

url = 'https://api.stormglass.io/v2/weather/point'
api_key = '4364a430-495b-11ec-b7e4-0242ac130002-4364a4a8-495b-11ec-b7e4-0242ac130002'

cur_date = datetime.now()
start_timepoint = datetime.timestamp(cur_date)
end_timepoint = datetime.timestamp(cur_date + timedelta(hours=12))

params = {
    'lat': 44.620532,
    'lng': 33.556023,
    'start': start_timepoint,
    'end': end_timepoint,
    'params': 'swellHeight',
}

result = requests.get(url,
                      params=params,
                      headers={
                          'Authorization': api_key,
                      }
                      )

json_data = result.json()
# pprint(json_data)

with open('api_data.json', 'w') as outfile:
    json.dump(json_data, outfile)

count = 0
for item in json_data['hours']:
    wave_height = json_data['hours'][count]['swellHeight']['sg']
    time_n_date = json_data['hours'][count]['time'].split(':', 1)[0].split('T')
    print(f'{time_n_date[0]} в {time_n_date[1]} ч. высота волн будет {wave_height} м')
    count += 1