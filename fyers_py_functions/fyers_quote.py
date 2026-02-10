
import datetime
from fyers_apiv3 import fyersModel

#generate trading session
client_id = open("client_ID.txt",'r').read()
access_token = open("access_token.txt",'r').read()

# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="D:\FyiersApiAutomation\logs")


# Fetch quote details
data = {
    "symbols":"NSE:SBIN-EQ,NSE:YESBANK-EQ"
}
response = fyers.quotes(data=data)
print(response)

stockname = response['d'][0]['n']
print("Stockname: ", stockname)

exchange = response['d'][0]['v']['exchange']
print("Exchange: ", exchange)

today_high_price = response['d'][0]['v']['high_price']
print("Today High Price: ", today_high_price)

today_low_price = response['d'][0]['v']['low_price']
print("Today Low Price: ", today_low_price)

today_open_price = response['d'][0]['v']['open_price']
print("Today Open Price: ", today_open_price)

prev_close_price = response['d'][0]['v']['prev_close_price']
print("Prev Close Price: ", prev_close_price)

today_volume = response['d'][0]['v']['volume']
print("Today Volume: ", today_volume)

ltp = response['d'][0]['v']['lp']
print("LTP: ", ltp)

bid = response['d'][0]['v']['bid']
print("Bid: ", bid)

ask = response['d'][0]['v']['ask']
print("Ask: ", ask)


stockname2 = response['d'][1]['n']
print("Stockname: ", stockname2)

exchange2 = response['d'][1]['v']['exchange']
print("Exchange: ", exchange2)

today_high_price2 = response['d'][1]['v']['high_price']
print("Today High Price: ", today_high_price2)

today_low_price2 = response['d'][1]['v']['low_price']
print("Today Low Price: ", today_low_price2)

today_open_price2 = response['d'][1]['v']['open_price']
print("Today Open Price: ", today_open_price2)

prev_close_price2 = response['d'][1]['v']['prev_close_price']
print("Prev Close Price: ", prev_close_price2)

today_volume2 = response['d'][1]['v']['volume']
print("Today Volume: ", today_volume2)

ltp2 = response['d'][1]['v']['lp']
print("LTP: ", ltp2)

bid2 = response['d'][1]['v']['bid']
print("Bid: ", bid2)

ask2 = response['d'][1]['v']['ask']
print("Ask: ", ask2)
