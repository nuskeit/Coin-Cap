from flask import Flask, request
from flask_cors import CORS
from binance.client import Client
from binance.enums import *
import config, json, sys, time
from markupsafe import escape
from decimal import Decimal
from coin_database_api import execute_sql, connect
from enum import Enum

# $Env:FLASK_APP="app.py" S
# $Env:FLASK_DEBUG=1
# $Env:FLASK_ENV="development"

app = Flask(__name__)
CORS(app)

class RunType(Enum):
  PROD = "PROD"
  TEST = "TEST"

# runType could be implemented as a parameter passed from the client.
runType = RunType.TEST
client = None

# PROD:
if runType == "PROD":
  client = Client(config.api_key, config.api_secret, tld='com')

# TEST:
elif runType == "TEST":
  client = Client(config.api_testnetKey, config.api_testnetSecret, tld='com', testnet=True)

### DEFAULT
@app.route('/')
def index():
  return "UP AND RUNNING"

### GET KEY
@app.route('/getkey')
def getkey():
  return json.dumps({"key":client.stream_get_listen_key()})


# ACCOUNT ENDPOINTS
### Daily account snapshot
@app.route('/get_account_snapshot')
def get_account_snapshot():
  info = client.get_account_snapshot(type='SPOT')
  accinfo_json = json.dumps(info)
  return accinfo_json

#Get account info
@app.route('/get_account_info')
def get_account_info():
  info = client.get_account()
  toJson = json.dumps(info)
  return toJson

#Get asset balance
@app.route('/get_balance/<asset>')
def get_balance(asset):
  balance = client.get_asset_balance(asset=asset)
  toJson = json.dumps(balance)
  return toJson


#Get account status
@app.route('/get_account_status')
def get_account_status():
  status = client.get_account_status()
  toJson = json.dumps(status)
  return toJson


#Get account API trading status
@app.route('/get_account_api_trading_status')
def get_account_api_trading_status():
  status = client.get_account_api_trading_status()
  toJson = json.dumps(status)
  return toJson


#Get recent trades
@app.route('/get_recent_trades/<pSymbol>')
def get_recent_trades(pSymbol):
  trades = client.get_recent_trades(symbol=pSymbol, limit=1000)
  toJson = json.dumps(trades)
  return toJson

@app.route('/get_symbol_info/<pSymbol>')
def get_symbol_info(pSymbol):
  trades = client.get_symbol_info(symbol=pSymbol)
  toJson = json.dumps(trades)
  return toJson




import itertools
from decimal import Decimal
#Get historical trades
@app.route('/get_simulator_trades/<pSymbol>')
def get_simulator_trades(pSymbol):
  try:
    response = []

    cnxn = connect()
    cursor = cnxn.cursor()
    rows = cursor.execute("""exec market_data_get_by_symbol ? """, pSymbol).fetchall()
    if len(rows) > 0:
      #response = [dict(row) for row in rows]
      for row in rows:
        response.append({'id': row[0], 'price': "{:0.0{}f}".format(row[2], 4), 'qty': "{:0.0{}f}".format(row[3], 4), 
                        'quoteQty': "{:0.0{}f}".format(row[4], 4), 
                        'time': row[5], 'isBuyerMaker': row[6], 'isBestMatch': row[7]})
    else:
      pFromId = None
      for _ in itertools.repeat(None, 10):
        trades = client.get_historical_trades(symbol=pSymbol, fromId=pFromId, limit=1000)
        pFromId = None
        for t in trades:
          if pFromId == None:
            pFromId = t["id"]-1000
          response.append({'id': t["id"], 'price': float(t["price"]), 'qty': float(t["qty"]), 
                          'quoteQty': float(t["quoteQty"]), 
                          'time': t["time"], 'isBuyerMaker': t["isBuyerMaker"], 'isBestMatch': t["isBestMatch"]})
          cursor.execute("""exec market_data_insert ?, ?, ?, ?, ?, ?, ?, ? """, t["id"], pSymbol, float(t["price"]), float(t["qty"]), float(t["quoteQty"]),
                           t["time"], t["isBuyerMaker"], t["isBestMatch"])
        cnxn.commit()

    cursor.close()
    cnxn.close()
    
    return json.dumps(response)
  
  except:
    e = sys.exc_info()
    return json.dumps({"success": False})
    pass

    

#Get my trades
@app.route('/get_my_trades/<pSymbol>')
def get_my_trades(pSymbol):
  trades = client.get_my_trades(symbol=pSymbol)
  toJson = json.dumps(trades)
  return toJson


#Get trade fees
# get fees for all symbols
@app.route('/get_trade_fees')
def get_trade_fees():
  fees = client.get_trade_fee()
  toJson = json.dumps(fees)
  return toJson

# get fee for one symbol
@app.route('/get_trade_fee/<pSymbol>')
def get_trade_fee(pSymbol):
  fee = client.get_trade_fee(symbol=pSymbol)
  toJson = json.dumps(fee)
  return toJson



#Get asset details
@app.route('/get_asset_details')
def get_asset_details():
  details = client.get_asset_details()
  toJson = json.dumps(details)
  return toJson


#Get dust log
@app.route('/get_dust_log')
def get_dust_log():
  log = client.get_dust_log()
  toJson = json.dumps(log)
  return toJson


#Transfer dust
@app.route('/transfer_dust/<pAsset>')
def transfer_dust(pAsset):
  transfer = client.transfer_dust(asset=pAsset)
  toJson = json.dumps(transfer)
  return toJson


#Get Asset Dividend History
@app.route('/get_asset_dividend_history')
def get_asset_dividend_history():
  history = client.get_asset_dividend_history()
  toJson = json.dumps(history)
  return toJson



# TRADE ENDPOINTS
@app.route('/test_get_purchase_amount')
def test_get_purchase_amount():
  try:
    
    cnxn = connect()
    cursor = cnxn.cursor()
    cursor.execute("""exec get_next_purchase_amount ? """, "USDT")

    row = cursor.fetchone()
    purchase_amount = row[0]
    return json.dumps({"success" : True, "data" : {"test_purchase_amount": purchase_amount}})

  except:
    e = sys.exc_info()
    return json.dumps({"success": False})



### Log orders
@app.route('/order_log', methods = ['POST'])
def order_log():
  try:
    content = request.get_json()
    
    # format price this way
    precision = 5
    response = execute_sql("""exec order_insert ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?  """, *list(content.values()))

    return json.dumps({"success": True})
  except:
    e = sys.exc_info()
    return json.dumps({"success": False})


### BUY
@app.route('/buy', methods = ['POST'])
def buy():
  try:
    content = request.get_json()
    
    # format price this way
    precision = 5
    response = execute_sql("""exec stop_limit_order_put ?, ?, ?, ?, ?, ? """, time.time(), content["symbol"], "BUY", 
                "{:0.0{}f}".format(content["amount"], precision), 
                "{:0.0{}f}".format(content["stop"], precision), 
                "{:0.0{}f}".format(content["limit"], precision))

    return json.dumps({"success": True})
  except:
    e = sys.exc_info()
    return json.dumps({"success": False})



#CREATE ORDERS:


## CREATE OCO ORDER
@app.route('/create_oco_order', methods = ['POST'])
def create_oco_order():
  order = client.create_oco_order(
      symbol='BNBBTC',
      side=SIDE_SELL,
      stopLimitTimeInForce=TIME_IN_FORCE_GTC,
      quantity=100,
      stopPrice='0.00001',
      price='0.00002')
  return None
  
@app.route('/create_limit_order', methods = ['POST'])
def create_limit_order():
  content = request.get_json()
  order=None
  try:
    if content["side"] =="BUY":
      order = client.order_limit_buy(
        symbol=content["symbol"],
        quantity=content["quantity"],
        price=content["price"])
    else:
      order = client.order_limit_sell(
        symbol=content["symbol"],
        quantity=content["quantity"],
        price=content["price"])
    return json.dumps(order)
  except:
    e = sys.exc_info()
    return json.dumps({"success": False})
  

@app.route('/create_market_order', methods = ['POST'])
def create_market_order():
  content = request.get_json()
  order=None
  try:
    if content["side"] =="BUY":
      order = client.order_market_buy(
        symbol=content["symbol"],
        quantity=content["quantity"])
    else:
      order = client.order_market_sell(
        symbol=content["symbol"],
        quantity=content["quantity"])
    return json.dumps(order)
  except:
    e = sys.exc_info()
    return json.dumps({"success": False})

  
@app.route('/create_test_order', methods = ['POST'])
def create_test_order():
  order = client.create_test_order(
    type=ORDER_TYPE_LIMIT,
    symbol=content["symbol"],
    side=content["side"],
    stopLimitTimeInForce=TIME_IN_FORCE_GTC,
    quantity=content["quantity"],
    stopPrice=None,
    price=content["price"])
  return json.dumps(order)

### CHECK ORDER
@app.route('/check_order/<pSymbol>/<pOrderId>', methods = ['GET'])
def check_order(pSymbol, pOrderId):
  order = client.get_order(
    symbol=pSymbol,
    orderId=pOrderId)
  return json.dumps(order)


### CANCEL ORDER
@app.route('/cancel_order/<pSymbol>/<pOrderId>', methods = ['GET'])
def cancel_order(pSymbol, pOrderId):
  order = client.cancel_order(
    symbol=pSymbol,
    orderId=pOrderId)
  return json.dumps(order)


### GET ALL ORDERS
@app.route('/get_all_orders/<pSymbol>/<pLimit>')
def get_all_orders(pSymbol, pLimit=10):
  accinfo = client.get_all_orders(symbol=pSymbol, limit=pLimit)
  accinfo_json = json.dumps(accinfo)
  return accinfo_json


### GET OPEN ORDERS
@app.route('/get_open_orders/<pSymbol>')
def get_open_orders(pSymbol):
  orders = client.get_open_orders(symbol=pSymbol)
  accinfo_json = json.dumps(orders)
  return accinfo_json


#================================================================
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#================================================================


#INFO ENDPOINTS

@app.route('/get_server_time')
def get_server_time():
  return client.get_server_time()

### GET ALL SYMBOLS
@app.route('/all_symbols')
def all_symbols():
  tickers = client.get_all_tickers()
  tickers_json = json.dumps(tickers)
  return tickers_json

### EXCHANGE INFO
@app.route('/exchange_info')
def exchange_info():
  info = client.get_exchange_info()
  info_json = json.dumps(info)
  return info_json

### GET KLINES
@app.route('/get_klines/<pSymbol>/<start>/<pLimit>')
def get_klines(pSymbol, start, pLimit):
  klines = client.get_klines(symbol=escape(pSymbol), interval=Client.KLINE_INTERVAL_1MINUTE, startTime=escape(start), limit=pLimit)
  return json.dumps(klines)

### GET HISTORICAL KLINES
@app.route('/aquire_historical_klines/<symbol>/<start>/<end>')
def aquire_historical_klines1(symbol, start, end=None):

  klines = None
  if end == None:
    klines = client.get_historical_klines(escape(symbol), Client.KLINE_INTERVAL_1MINUTE, escape(start))
  else:
    klines = client.get_historical_klines(escape(symbol), Client.KLINE_INTERVAL_1MINUTE, escape(start), escape(end))
  klines_json = json.dumps(klines)
  return klines_json


### GET HISTORICAL CANDLESTICKS WITH SIMPLE PATTERN IDENTIFICATION
from candlestick_patterns import identifyCandlestickPattern, CandleStickType
# Returns ohlc data with simple pattern identification
@app.route('/aquire_historical_klines_with_spi/<symbol>/<start>/<end>')
def aquire_historical_klines_with_spi(symbol, start, end=None):
  try :
    if symbol != None and symbol != "" and start != None and start != "" :
      klines = None
      if end == None:
        klines = client.get_historical_klines(escape(symbol), Client.KLINE_INTERVAL_1MINUTE, escape(start))
      else:
        klines = client.get_historical_klines(escape(symbol), Client.KLINE_INTERVAL_1MINUTE, escape(start), escape(end))

      maxMarket = Decimal(0)
      minMarket = Decimal(9999999999999)
      for x in klines:
        auxl = x[1:5]
        maxMarket = max(maxMarket, Decimal(auxl[0]), Decimal(auxl[1]), Decimal(auxl[2]), Decimal(auxl[3]))
        minMarket = min(minMarket, Decimal(auxl[0]), Decimal(auxl[1]), Decimal(auxl[2]), Decimal(auxl[3]))

      for k in klines:
        patternName = identifyCandlestickPattern(Decimal(k[1]),Decimal(k[2]),Decimal(k[3]),Decimal(k[4]), Decimal(minMarket), Decimal(maxMarket))
        k.append(patternName)

      klines_json = json.dumps(klines)
      return klines_json
    else :
      return json.dumps('{"message": "NO PARAMS"}')
  except :
    return json.dumps('{"message": "ERROR"}')

### IDENTIFIES A SINGLE CANDLESTICK PATTERN
@app.route('/decode_single_candle/<o>/<h>/<l>/<c>/<minMarket>/<maxMarket>')
def decode_single_candle(o,h,l,c, minMarket, maxMarket):

  k = identifyCandlestickPattern(Decimal(o),Decimal(h),Decimal(l),Decimal(c), Decimal(minMarket), Decimal(maxMarket))

  k_json = json.dumps(k)
  return k_json


### GET HISTORICAL CANDLESTICKS
@app.route('/aquire_historical_klines/<symbol>/<start>')
def aquire_historical_klines2(symbol, start):
  return aquire_historical_klines1(symbol, start)
  
  

