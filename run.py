from functions import *
from datetime import date
import sys

def check_date(d):
    try:
        result_date = datetime.strptime(d+' 00:00', time_format)
        if result_date.date() > date.today():
            print("It's a future time, please input a date in the past:")
            return False
        elif result_date.date() < date(2010,6,13):
            print('The earliest data available is from 2010-6-13, please input a date later than this:')
        else:
            return result_date.date()
    except ValueError:
        print('Please input a valid date!')
        return False


def check_g_type(g_type):
    while True:
        if g_type not in {'c', 'f', 'cf', 'm'}:
            print('only commands below are valid:')
            g_type = input(g_select)
        else:
            return g_type


# Main Scripts
print('Welcome to CME & FLR event simple visualization python script!')
print('Please input the data time period below\nFormat: yyyy-mm-dd')
while True:
    start = input('Start Date:')
    start_date_d = check_date(start)
    if start_date_d is False:
        continue

    end = input('End Date:')
    end_date_d = check_date(end)
    if end_date_d is False:
        continue

    if start_date_d is not False and end_date_d is not False:
        break
print('Loading data from cache...\n')

start_date = start_date_d.strftime('%Y-%m-%d')
end_date = end_date_d.strftime('%Y-%m-%d')

cme_file = 'cache/cme_from_{}_to_{}.json'.format(start_date, end_date)
flr_file = 'cache/flr_from_{}_to_{}.json'.format(start_date, end_date)
cc_file = 'cache/correlations_from_{}_to_{}.json'.format(start_date, end_date)

try:
    cme, flr, cc = load_cache(cme_file, flr_file, cc_file)
except FileNotFoundError:
    print('Data not found in cache, fetching data from DONKI...\n')
    cme = get_cme(start_date, end_date)
    flr = get_flr(start_date, end_date)
    store_cache(cme, flr, start_date, end_date)
t = input('Enter a threshold you want to use to calculate the correlation coefficient\nThe threshold must be '
          'a float from 0 to 1:\n')

while True:
    try:
        cc_threshold = float(t)
        if cc_threshold < 0 or cc_threshold > 1:
            t = input('threshold out of range, from 0 to 1:\n')
            continue
        else:
            break
    except TypeError:
        t = input('Please input a valid number:\n')

if cc_threshold == 0.01:
    with open(cc_file) as f:
        cc = json.load(f)
        print('correlations loading complete! totally {} correlations loaded.'.format(len(cc)))
else:
    cc = calculate_all_cc(cme, flr, cc_threshold)

print('Data process complete! Select a graph below you want to see, use the letter command below:')
g_select = 'c  - CME Density\nf  - FLR Density\ncf - Density Comparison\nm  - Events Correlation Map\n'
g_type = input(g_select)
g_type = check_g_type(g_type)

while True:
    if g_type == 'c':
        plot_event_density(cme, 'CME')
    elif g_type == 'f':
        plot_event_density(flr, 'FLR')
    elif g_type == 'cf':
        plot_both_density(cme, flr)
    elif g_type == 'm':
        plot_network(cme, flr, cc)
    print('Any other graph you want to see? type "no" to exit the program')
    g_type = input(g_select)
    if g_type == 'no':
        break
    g_type = check_g_type(g_type)

print('Thanks for using')
sys.exit(0)



