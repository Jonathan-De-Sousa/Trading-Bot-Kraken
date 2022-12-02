"""
Trading Bot

* Version 2
* Main objectives: implement random trading strategy into paper trader
* Trading strategy: buy and sell at random time intervals between 1 and 20 min 

Created on Sun Sept 26 18:18:00 2021
Written by: Jonathan De Sousa 
"""

import krakenex
import json
import time
import datetime
import calendar
import math 
from random import random

kraken_fee = 0.0026 # global variable

def get_crypto_data(pair, since):
    # OHLC = Opening, Highest, Lowest, Closing prices for each time period
    return api.query_public('OHLC', data = {'pair':pair , 'since':since})['result'][pair]

def analyse(pair, since):
    balance = get_fake_balance()
    last_trade = get_last_trade(pair[0]+pair[1])
    
    close_ = float(get_crypto_data(pair[0]+pair[1], since)[0][4])
    
    did_sell = False
    
    # Sell logic
    if float(balance['XETH']) > 0:
        fake_sell(pair, close_, last_trade)
        did_sell = True
    
    # Buy logic
    if not did_sell and float(balance['ZGBP']) > 0:
        # Spend 99.74% of fiat capital
        # Always set below 99.74% to account for trading fees 
        fiat_amount = float(balance['ZGBP']) * 0.9974
        fake_buy(pair, fiat_amount, close_, last_trade)


# Once paper trader works, replace every instance of get_fake_**() with 
# get_**()        
def get_balance():
    return api.query_private('Balance')['result']

def get_fake_balance():
    # Open .json file for reading ('r') and assign as object j
    with open('balance.json', 'r') as f:
        # load json object as Python dictionary
        return json.load(f)

# Balance needs to be updated for paper trader - in real trading balance
# on Kraken is automatically updated
def fake_update_balance(pair, fiat_amount, close_, trade_type, last_trade):
    balance = get_fake_balance()
    
    crypto_balance = float(balance['XETH'])
    fiat_balance = float(balance['ZGBP'])

    crypto_vol = float(last_trade['vol'])
    
    if trade_type == 'sell':
        crypto_balance -= crypto_vol
        fiat_balance += fiat_amount * (1 - kraken_fee) 
    elif trade_type == 'buy':
        crypto_balance += crypto_vol
        fiat_balance -= fiat_amount * (1 + kraken_fee)
           
    balance['XETH'] = str(crypto_balance) 
    balance['ZGBP'] = str(fiat_balance)
    
    print("-----Balance-----")
    print("Type: ", trade_type)
    print("XETH: ", balance['XETH'])
    print("ZGBP: ", balance['ZGBP'])
    
    with open('balance.json', 'w') as f:
        json.dump(balance, f, indent=4)
        
        

# Buys with only 50% of fiat capital (SEE analyse() function)
def fake_buy(pair, fiat_amount, close_, last_trade):
    trades_history = get_fake_trades_history()
    last_trade['price'] = str(close_)
    last_trade['type'] = 'buy'
    last_trade['cost'] = str(fiat_amount)
    last_trade['fee'] = str(fiat_amount * kraken_fee)
    last_trade['time'] = datetime.datetime.now().timestamp()
    last_trade['vol'] = str(fiat_amount/close_)
    
    time.sleep(0.001) #DO NOT REMOVE - prevents timestamp-related issue with recording trades
    trades_history['result']['trades'][str(datetime.datetime.now().timestamp()*10)] = last_trade
    with open('tradeshistory.json', 'w') as f:
        json.dump(trades_history, f, indent=4)
    
    fake_update_balance(pair, fiat_amount, close_, 'buy', last_trade)
        
    # to do real buy/sell, code is something like: 
    """api.query_private()"""
    # look at Kraken API website for what the arg is 
    
# Sell all cryptocurrency from last buy trade
def fake_sell(pair, close_, last_trade):
    balance = get_fake_balance()
    cost = float(balance['XETH']) * close_
    
    trades_history = get_fake_trades_history()
    last_trade['price'] = str(close_)
    last_trade['type'] = 'sell'
    last_trade['cost'] = str(cost)
    last_trade['fee'] = str(cost * kraken_fee)
    last_trade['time'] = datetime.datetime.now().timestamp()
    last_trade['vol'] = (balance['XETH']) 
    
    time.sleep(0.001) #DO NOT REMOVE - prevents timestamp-related issue with recording trades
    trades_history['result']['trades'][str(datetime.datetime.now().timestamp())] = last_trade
    with open('tradeshistory.json', 'w') as f:
        json.dump(trades_history, f, indent=4)
    
    fake_update_balance(pair, cost, close_, 'sell', last_trade)
    


# date_nix() & req() process dates & times specific to the API  interpretation    
def date_nix(str_date):
    return calendar.timegm(str_date.timetuple())

def req(start, end, ofs):
    req_data = {
        'type': 'all',
        'trades': 'true',
        'start': str(date_nix(start)),
        'end': str(date_nix(end)),
        'ofs': str(ofs)
    }
    return req_data

def get_trades_history():
    start_date = datetime.datetime(2020, 1, 1)
    end_date = datetime.datetime.today()
    return api.query_private('TradesHistory', req(start_date, end_date, 1))['result']['trades']

def get_fake_trades_history():
    with open('tradeshistory.json', 'r') as f:
        return json.load(f)
    
# Last trade refers to last buy trade
def get_last_trade(pair):
    trades_history = get_fake_trades_history()['result']['trades']
    
    last_trade = {}
    
    for TRADE in trades_history:
        trade = trades_history[TRADE]
        if trade['pair'] == pair and trade['type'] == 'buy':
            last_trade = trade
    
    return last_trade

    

def reset_fake_data():
    # Reset fake balance
    balance = get_fake_balance()
    close_ = float(get_crypto_data('XETHZGBP', str(int(time.time())))[0][4])
    
    balance['XETH'] = '0.05000000' 
    balance['ZGBP'] = '100.000000'
    balance['Intial fiat value'] = str(close_ * float(balance['XETH']) + float(balance['ZGBP'])) 
    
    with open('balance.json', 'w') as f:
        json.dump(balance, f, indent=4)
    
    # Reset fake trades history
    current_time = time.time()
    
    pair = ('XETHZGBP')
    since = str(int(current_time))
    
    trades_history = get_fake_trades_history()
    data = get_crypto_data(pair, since)
    
    first_trade = {}
    first_trade['ordertxid'] = 'OQCLML-BW3P3-BUCMWZ' # fictitious
    first_trade['postxid']   = 'TKH2SE-M7IF5-CFI7LT' # fictitious
    first_trade['pair']      = pair
    first_trade['time']      = current_time
    first_trade['type']      = 'buy'
    first_trade['ordertype'] = 'market'
    first_trade['price']     = data[0][3] # current closing price
    first_trade['cost']      = str(float(balance['XETH'])*float(data[0][3]))
    first_trade['fee']       = str(float(balance['XETH'])*float(data[0][3])*kraken_fee)
    first_trade['vol']       = balance['XETH']
    first_trade['margin']    = '0.00000'
    first_trade['misc']      = ''
    
    trades_history['result']['trades'].clear()
    trades_history['result']['trades'][str(current_time)] = first_trade
    with open('tradeshistory.json', 'w') as f:
        json.dump(trades_history, f, indent=4)
        
def verify_trades_history():
    trades_history = get_fake_trades_history()['result']['trades']
    
    crypto_balance = 0.05
    fiat_balance = 100
    count = 0
    
    for TRADE in trades_history:
        if count != 0:
            if trades_history[TRADE]['type'] == 'buy': 
                crypto_balance += float(trades_history[TRADE]['vol'])
                fiat_balance -= float(trades_history[TRADE]['cost']) + float(trades_history[TRADE]['fee'])
            else:
                crypto_balance -= float(trades_history[TRADE]['vol'])
                fiat_balance += float(trades_history[TRADE]['cost']) - float(trades_history[TRADE]['fee'])
        count += 1
    return crypto_balance, fiat_balance
    
 
    
if __name__ == '__main__':
    api = krakenex.API() # instantiate API (i.e. krakenex library)
    api.load_key('kraken.key') # load API keys
    
    pair = ("XETH", "ZGBP") # to analyse multiple pairs, make pair an array
    
    reset_fake_data()
    N_trades = 1 #100 #number of trades to execute
    
    for count in range(N_trades):
        since = str(int(time.time()))
        analyse(pair, since)
        
        # Pause is random number of minutes between 1 and 20
        # time.sleep(math.ceil(random() * 20 * 60))
        time.sleep(math.ceil(random() * 20 * 1))
        
    # Ensure all crypto sold in the end
    balance = get_fake_balance()
    if float(balance['XETH']) > 0:
        since = str(int(time.time()))
        close_ = get_crypto_data(pair[0]+pair[1], since)[0][4]
        last_trade = get_last_trade(pair[0]+pair[1])
        fake_sell(pair, close_, last_trade)
    
    print("")
    print("Crypto balance:", verify_trades_history()[0]) 
    print("Fiat balance  :", verify_trades_history()[1])    