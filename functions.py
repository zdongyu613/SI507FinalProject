import json
import API
import requests as req
import re
from datetime import datetime
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import networkx as nx
import numpy as np
from pandas import DataFrame
import math

KEY = API.key
CME_URL = API.cme
FLR_URL = API.flr

start_date = '2017-01-01'
end_date = '2021-11-30'
time_format = '%Y-%m-%d %H:%M'
cc_threshold = 0.01


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
    d = decode_cme_raw(raw)
    print('organization complete! totally {} cme events during {} to {}\n'.format(len(d), start_date, end_date))

    return d


def decode_cme_raw(raw):
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
            'cid': 'C{}'.format(cid),
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
    d = decode_flr_raw(raw)
    print('organization complete! totally {} flr events during {} to {}\n'.format(len(d), start_date, end_date))

    return d


def decode_flr_raw(raw):
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
            'fid': 'F{}'.format(fid),
            'time': stored_time,
            'lat': lat,
            'lon': lon
        }
        d.append(j)
        fid += 1

    return d


def store_cache(cme, flr):
    print('storing data from local cache...\n')
    with open('cme_from_{}_to_{}.json'.format(start_date, end_date), 'w') as c:
        c.write(json.dumps(cme))
        print('cme storing complete! totally {} events stored.'.format(len(cme)))
    with open('flr_from_{}_to_{}.json'.format(start_date, end_date), 'w') as f:
        f.write(json.dumps(flr))
        print('flr storing complete! totally {} events stored.'.format(len(flr)))
    with open('correlations_from_{}_to_{}.json'.format(start_date, end_date), 'w') as cc:
        c_list = calculate_all_cc(cme, flr, cc_threshold)
        cc.write(json.dumps(c_list))
        print('correlations storing complete! totally {} correlations stored'.format(len(c_list)))
        print('')

    return 0


def load_cache(cmefile, flrfile, ccfile):
    with open(cmefile) as c:
        print('loading cme...')
        cme = json.load(c)
        print('cme loading complete! totally {} events loaded.'.format(len(cme)))
    with open(flrfile) as f:
        print('loading flr...')
        flr = json.load(f)
        print('flr loading complete! totally {} events loaded.'.format(len(flr)))
    with open(ccfile) as cc:
        print('loading correlations...')
        coef = json.load(cc)
        print('correlations loading complete! totally {} correlations loaded.'.format(len(coef)))
    return cme, flr, coef


def calculate_time_correlation(cme_event, flr_event):
    causation = 1
    c_time = mdates.date2num(cme_event['time'])
    f_time = mdates.date2num(flr_event['time'])
    dt = c_time - f_time
    if abs(dt) > 40:
        return 0
    if dt < 0:
        causation = 0
    relation = 1 / math.pow(2, math.sqrt(abs(dt)))

    return causation, relation


def calculate_position_correlation(cme_event, flr_event):
    c_lat, c_lon = cme_event['lat'], cme_event['lon']
    f_lat, f_lon = flr_event['lat'], flr_event['lon']

    dlat = math.radians(c_lat - f_lat)
    dlon = math.radians(c_lon - f_lon)

    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(c_lat)) \
        * math.cos(math.radians(f_lat)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return 1 / math.pow(2, c ** 2)


def calculate_correlation_coefficient(cme_event, flr_event, threshold):
    time_cc = calculate_time_correlation(cme_event, flr_event)
    if time_cc == 0:
        return None
    pos_cc = calculate_position_correlation(cme_event, flr_event)
    cid = cme_event['cid']
    fid = flr_event['fid']
    cc = time_cc[1] * pos_cc
    if cc < threshold:
        return None
    if time_cc[0] == 0:
        cc *= -1
    return cid, fid, cc


def calculate_all_cc(cme_list, flr_list, threshold):
    cc_list = []
    print('calculating all correlation coefficients...')
    for i in cme_list:
        for j in flr_list:
            coef = calculate_correlation_coefficient(i, j, threshold)
            if coef is not None:
                cc_list.append(coef)
    print('calculating complete! totally {} valid correlations found.'.format(len(cc_list)))
    return cc_list

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
    # store_cache(get_cme(), get_flr())
    cme, flr, cc = load_cache(
        'cme_from_2017-01-01_to_2021-11-30.json',
        'flr_from_2017-01-01_to_2021-11-30.json',
        'correlations_from_2017-01-01_to_2021-11-30.json'
    )
