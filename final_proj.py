import json
import API
import requests as req
import re
from datetime import datetime
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from pandas import DataFrame

KEY = API.key
CME_URL = API.cme
FLR_URL = API.flr

start_date = '2017-01-01'
end_date = '2021-11-30'
time_format = '%Y-%m-%d %H:%M'


def get_cme():
    parameters = {
        'startDate': start_date,
        'endDate': end_date,
        'api_key': KEY
    }
    print('Fetching data from CMEAnalysis...')
    r = req.get(CME_URL, params=parameters)
    raw = r.json()
    print('raw data collected!')

    print('organizing json...')
    d = load_cme_raw(raw)
    print('organization complete!')

    return d


def load_cme_raw(raw):
    d = []
    cid = 0
    for i in raw:
        sep = i['time21_5'].split('T')
        dat = sep[0].split('-')
        t = sep[1].rstrip('Z').split(':')
        formated_time = datetime(
            year=int(dat[0]),
            month=int(dat[1]),
            day=int(dat[2]),
            hour=int(t[0]),
            minute=int(t[1])
        )

        stored_time = formated_time.strftime(time_format)

        j = {
            'cid': cid,
            'time': stored_time,
            'lat': round(i['latitude']),
            'lon': round(i['longitude'])
        }
        d.append(j)
        cid += 1

    return d


def get_flr():
    parameters = {
        'startDate': start_date,
        'endDate': end_date,
        'api_key': KEY
    }
    print('Fetching data from FLR...')
    r = req.get(FLR_URL, params=parameters)
    raw = r.json()
    print('raw data collected!')

    print('organizing json...')
    d = load_flr_raw(raw)
    print('organization complete!')

    return d


def load_flr_raw(raw):
    d = []
    fid = 0
    for i in raw:
        sep = i['peakTime'].split('T')
        dat = sep[0].split('-')
        t = sep[1].rstrip('Z').split(':')
        formated_time = datetime(
            year=int(dat[0]),
            month=int(dat[1]),
            day=int(dat[2]),
            hour=int(t[0]),
            minute=int(t[1])
        )

        stored_time = formated_time.strftime(time_format)

        pos = re.findall(r'([A-Z]\d*)', i['sourceLocation'])
        lat = 0
        lon = 0
        if 'S' in pos[0]:
            lat -= int(pos[0][1:])
        elif 'N' in pos[0]:
            lat += int(pos[0][1:])
        if 'W' in pos[1]:
            lon -= int(pos[1][1:])
        elif 'E' in pos[1]:
            lon += int(pos[1][1:])

        j = {
            'fid': fid,
            'time': stored_time,
            'lat': lat,
            'lon': lon
        }
        d.append(j)
        fid += 1

    return d


def store_cache(cme, flr):
    with open('cme_from{}to{}.json'.format(start_date, end_date), 'w') as c:
        c.write(json.dumps(cme))
    with open('flr_from{}to{}.json'.format(start_date, end_date), 'w') as f:
        f.write(json.dumps(flr))
    return 0


def load_cache(cmefile, flrfile):
    with open(cmefile) as c:
        cme = json.load(c)
    with open(flrfile) as f:
        flr = json.load(f)
    return cme, flr


def calculate_correlation_coefficient(cme_event, flr_event):
    pass


def plot_event_density(events, event_name):
    t_series = [datetime.strptime(i['time'], time_format) for i in events]
    p_series = [mdates.date2num(i) for i in t_series]

    t_data = DataFrame(p_series, columns=[event_name])

    ax = t_data.plot(kind='kde')
    ax.set_xbound(mdates.date2num(start_date), mdates.date2num(end_date))
    x_ticks = ax.get_xticks()[::2]
    ax.set_xticks(x_ticks)
    x_label = [mdates.num2date(i).date() for i in x_ticks]
    ax.set_xticklabels(x_label)
    ax.set_xlabel('Dates')
    ax.set_ylabel('Relative Density')
    ax.set_yticks([])

    plt.show()


def plot_both_density(cme, flr):
    pass


if __name__ == '__main__':
    store_cache(cme=get_cme(),flr=get_flr())
