#!/usr/local/bin/python3

# Author: Zebing Lin (https://github.com/linzebing)

from datetime import datetime, date
import math
import numpy as np
import time
import sys
import requests

if len(sys.argv) == 1:
    symbols = ['UPRO', 'TMF']
else:
    symbols = sys.argv[1].split(',')
    for i in range(len(symbols)):
        symbols[i] = symbols[i].strip().upper()

num_trading_days_per_year = 252
window_size = 20
date_format = "%Y-%m-%d"
end_timestamp = int(time.time())
start_timestamp = int(end_timestamp - (1.4 * (window_size + 1) + 4) * 86400)


def get_volatility_and_performance_and_price(symbol):
    download_url = "https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history&crumb=a7pcO//zvcW".format(symbol, start_timestamp, end_timestamp)
    lines = requests.get(download_url, cookies={'B': 'chjes25epq9b6&b=3&s=18'}).text.strip().split('\n')
    assert lines[0].split(',')[0] == 'Date'
    assert lines[0].split(',')[4] == 'Close'
    prices = []
    for line in lines[1:]:
        prices.append(float(line.split(',')[4]))
    prices.reverse()
    volatilities_in_window = []

    for i in range(window_size):
        volatilities_in_window.append(math.log(prices[i] / prices[i+1]))
        
    most_recent_date = datetime.strptime(lines[-1].split(',')[0], date_format).date()
    assert (date.today() - most_recent_date).days <= 4, "today is {}, most recent trading day is {}".format(date.today(), most_recent_date)

    return np.std(volatilities_in_window, ddof = 1) * np.sqrt(num_trading_days_per_year), prices[0] / prices[window_size] - 1.0, prices[0]

volatilities = []
performances = []
prices = []
sum_inverse_volatility = 0.0
for symbol in symbols:
    volatility, performance, price = get_volatility_and_performance_and_price(symbol)
    sum_inverse_volatility += 1 / volatility
    volatilities.append(volatility)
    performances.append(performance)
    prices.append(price)

print ("Portfolio: {}, as of {} (window size is {} days)".format(str(symbols), date.today().strftime('%Y-%m-%d'), window_size))
allocations = []
for i in range(len(symbols)):
    allocation = float(1 / (volatilities[i] * sum_inverse_volatility))
    allocations.append(allocation)
    print ('{} allocation ratio: {:.2f}% (price: ${:.2f}, anualized volatility: {:.2f}%, performance: {:.2f}%)'.format(symbols[i], allocation * 100.0, float(prices[i]), float(volatilities[i] * 100), float(performances[i] * 100)))

# Rebalance Strategy
# Author: qxx (https://github.com/qxx)

my_shares = []
for i in range(len(symbols)):
    share = float(input(symbols[i] + " Quantity: "))
    my_shares.append(share)

cash = float(input("Cash: "))
cash_keep = float(input("Minimal Cash wish to keep: "))

my_value = cash
for i in range(len(symbols)):
    my_value = my_value + my_shares[i] * prices[i]

print("My value: {:.2f}".format(my_value))

target_shares = []
share_changes = []
for i in range(len(symbols)):
    # round down to the nearest whole share
    target_share = int((my_value - cash_keep) * allocations[i] / prices[i])
    target_shares.append(target_share)
    share_changes.append(target_share - my_shares[i])

for i in range(len(symbols)):
    cash = cash - share_changes[i] * prices[i]
    target_percent =  target_shares[i] * prices[i] * 100 / my_value
    if(share_changes[i] > 0):
        print ('{} buy {} shares -> {:.2f}%'.format(symbols[i], share_changes[i], target_percent))
    elif(share_changes[i] < 0):
        print ('{} sell {} shares -> {:.2f}%'.format(symbols[i], share_changes[i], target_percent))
    else:
        print ('{} no change -> {:.2f}%'.format(symbols[i], target_percent))

print ('Cash remain: ${:.2f}'.format(cash))