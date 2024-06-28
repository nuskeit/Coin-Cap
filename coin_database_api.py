from binance.client import Client
from markupsafe import escape
import pyodbc 
import config
import sys
#from datetime import datetime

client = Client(config.api_key, config.api_secret, tld='com')

def connect():
  return pyodbc.connect('DRIVER='+config.db_driver+';SERVER='+config.server+';DATABASE='+config.database+';UID='+config.username+';PWD='+ config.password)

def execute_sql(command_text, *parameters):
  try:
    cnxn = connect()
    cursor = cnxn.cursor()

    cursor.execute(command_text, *parameters)

    cnxn.commit()

    return cursor

  except:
    cnxn.rollback()
    e = sys.exc_info()[0]
    return {"error execute_sql": e}

def acquire_historical_klines(symbol, interval, start, end=None):
  klines = None
  if end == None:
    klines = client.get_historical_klines(escape(symbol), interval, escape(start))
  else:
    klines = client.get_historical_klines(escape(symbol), interval, escape(start), escape(end))

  try:
    cnxn = connect()
    cursor = cnxn.cursor()

    count = 0
    for k in klines:
      count += cursor.execute("""
      exec kline_insert ?,?,?,?,?,?,?,?,?,?,?,?,?,?""", symbol, interval, *k
      ).rowcount

    cnxn.commit()

  except:
    cnxn.rollback()
    e = sys.exc_info()[0]


def top_up_historical_klines(symbol, interval, force_start = None):
  try:
    if (force_start == None):
      cnxn = connect()
      cursor = cnxn.cursor()
      cursor.execute(""" exec kline__last_row ?, ? """, symbol, interval)
      row = cursor.fetchone()
      start = row[0]
      if start == None:
        start = "2021-01-01 00:00:00"
    else:
      start = force_start

    acquire_historical_klines(symbol, interval, start)
  except:
    e = sys.exc_info()[0]

