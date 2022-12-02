"""
Trading Bot

* Version 1
* Main objectives:  - set up paper trader to work properly
                    - verify paper trader's trading history matches crypto & fiat balances
* Trading strategy: simple (not recommended in reality)

Created on Thu Jul 22 11:45:48 2021
Written by: Jonathan De Sousa 
"""

import krakenex
import json
import time
import datetime
import calendar 

kraken_fee = 0.0026 # global variable

def get_crypto_data(pair, since):
    # Only include 'result' and, therewithin, the price pair from API call
    # OHLC = Opening, Highest, Lowest, Closing prices for each time period
    return api.query_public('OHLC', data = {'pair':pair , 'since':since})['result'][pair]

def analyse(pair, since):
    # '+' concatenates pair[0] & pair[1] to give "XETHZGBP"
    data = get_crypto_data(pair[0]+pair[1], since) 
    
    lowest = 0
    highest = 0
    
    for prices in data:
        balance = get_fake_balance()
        last_trade = get_last_trade(pair[0]+pair[1])
        last_trade_price = float(last_trade['price'])
        
        open_ = float(prices[1])
        high_ = float(prices[2])
        low_ = float(prices[3])
        close_ = float(prices[4])
        
        did_sell = False
        selling_point_profit = last_trade_price * 1.005
        selling_point_loss = last_trade_price * 0.995 # stop loss
        
        # Sell logic
        if float(balance['XETH']) > 0:
            # Sell at a profit
            if open_ >= selling_point_profit or close_ >= selling_point_profit:
                fake_sell(pair, close_, last_trade)
                did_sell = True
            # Sell at a loss
            elif open_ <= selling_point_loss or close_ <= selling_point_loss:
                fake_sell(pair, close_, last_trade)
                did_sell = True
        
        # Buy logic
        # Check if did not sell else may be instance where bot sells then 
        # immediately buys again, wasting money in fees
        if not did_sell and float(balance['ZGBP']) > 0:
            if low_ <= lowest or lowest == 0:
                lowest = low_
            if high_ > highest:
                highest = high_
                
            priceRatio__buy = 1.000
            
            if highest/lowest >= priceRatio__buy and low_ <= lowest:
                # Spend 50% of fiat capital
                # Always set below 99.74% to account for trading fees 
                fiat_amount = float(balance['ZGBP']) * 0.5
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
    
    balance['XETH'] = '0.05000000' 
    balance['ZGBP'] = '100.000000'
    
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
    since = str(int(time.time() - 3600/3600*60*100))
    
    # json.dumps() converts a Python object into a json string.
    # Console-displayed get_crypto_data: timestamp (seconds since Unix epoch: 
    # 1 Jan 1970, 00:00 UCT), then prices in OHLC order
    # print(json.dumps(get_crypto_data(pair[0]+pair[1], since), indent=4))
    
    # Before creating bot, real Kraken balances were:
        # ZGBP: 92.1639
        # XXRP: 1173
        # XETH: 3.09591
    # print(json.dumps(get_balance(), indent=4)) # displays 'error' if balance is zero
    
    # print(json.dumps(get_fake_balance(), indent=4))
    # print(json.dumps(get_trades_history(), indent=4))
    # print(json.dumps(get_fake_trades_history(), indent=4))
    
    
    # Insert while loop for continuous running of bot
    # Insert since variable into while loop to continuously update values
    # while True:
    reset_fake_data()
    analyse(pair, since)
    
    print("")
    print("Crypto balance:", verify_trades_history()[0]) 
    print("Fiat balance  :", verify_trades_history()[1])    
