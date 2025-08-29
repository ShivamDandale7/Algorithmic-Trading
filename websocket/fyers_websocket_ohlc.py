"""
NOTE: ON RE-RUNNING THIS SCRIPT, THE OLD OHLC CSVS WILL BE OVERWRITTEN
PLEASE STORE THE OLD CSVS SOMEWHERE SAFE THEN YOU CAN PROCEED
"""

from fyers_apiv3.FyersWebsocket import data_ws
from fyers_apiv3 import fyersModel
from datetime import datetime,timedelta
import pandas as pd
import threading
from pytz import timezone
import time
import pandas as pd
from csv import DictWriter
import os

#generate trading session
client_id = open("client_ID.txt",'r').read()
access_token = open("access_token.txt",'r').read()

timeframe = 1   # timeframe in minutes

ohlc_data = {}

csv_data = {} 

# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")

timeframe_counter = 1

def onmessage(message):

    global timeframe_counter
    global timeframe

    print("Response", message)
    ms = message['exch_feed_time']
    curr_time = datetime.fromtimestamp(ms)
    print("message exch_feed_time:", curr_time)

    if curr_time.second == 0:
        timeframe_counter += 1
    
    if timeframe_counter == timeframe:
        for symbol in ohlc_data:
            try:
                # find ohlc and save in csv
                high = max(ohlc_data[symbol])
                low = min(ohlc_data[symbol])
                open = ohlc_data[symbol][0]
                close = ohlc_data[symbol][-1]

                #print(ohlc_data[symbol])
                csv_dict = {'minute': str(curr_time), 'symbol': str(symbol),
                            'open': float(open), 'high': float(high),
                            'low': float(low), 'close': float(close), }

                if csv_data.get(symbol) == None:
                    csv_data[symbol] = []

                csv_data[symbol].append(csv_dict)
                df_dictionary = pd.DataFrame(csv_data[symbol])
                df_dictionary.to_csv(f'{symbol.replace(":", "_")}.csv')

                #generate_csv(symbol.replace(":", "_"), ['symbol', 'high', 'low', 'open', 'close', 'minute'], csv_dict)

                print("CSV MADE")
                print(csv_dict)

            except Exception as e:
                print(e)
            
            ohlc_data[symbol] = []

        timeframe_counter = 0

    else:
        if ohlc_data.get(message['symbol']) == None:
            ohlc_data[message['symbol']] = []
        
        ohlc_data[message['symbol']].append(float(message['ltp']))
        print(ohlc_data)


def onerror(message):
    print("Error:", message)

def onclose(message):
    print("Connection closed:", message)

def onopen():
    data_type = "SymbolUpdate"

    # Subscribe to the specified symbols and data type
    symbols = ['NSE:HDFCBANK-EQ']
    fyers.subscribe(symbols=symbols, data_type=data_type)

    # Keep the socket running to receive real-time data
    fyers.keep_running()

def generate_csv(csv_name, field_names, dict):

    if not os.path.isfile(f'{csv_name}.csv'):
        with open(f'{csv_name}.csv', 'a', newline='') as obj:
            dictwriter_object = DictWriter(obj, fieldnames=field_names)
            dictwriter_object.writeheader()
            dictwriter_object.writerow(dict)
            obj.close()
    else:
        with open(f'{csv_name}.csv', 'a', newline='') as obj:
            dictwriter_object = DictWriter(obj, fieldnames=field_names)
            dictwriter_object.writerow(dict)
            obj.close()

# Create a FyersDataSocket instance with the provided parameters
fyers = data_ws.FyersDataSocket(
    access_token=access_token,       # Access token in the format "appid:accesstoken"
    log_path="",                     # Path to save logs. Leave empty to auto-create logs in the current directory.
    litemode=False,                  # Lite mode disabled. Set to True if you want a lite response.
    write_to_file=False,              # Save response in a log file instead of printing it.
    reconnect=True,                  # Enable auto-reconnection to WebSocket on disconnection.
    on_connect=onopen,               # Callback function to subscribe to data upon connection.
    on_close=onclose,                # Callback function to handle WebSocket connection close events.
    on_error=onerror,                # Callback function to handle WebSocket errors.
    on_message=onmessage             # Callback function to handle incoming messages from the WebSocket.
)

# Establish a connection to the Fyers WebSocket

def main():
    print("Inside main()")
    fyers.connect()

main()