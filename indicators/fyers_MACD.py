import pandas as pd
import datetime as dt 
from fyers_apiv3 import fyersModel
import pytz
import  matplotlib.pyplot as plt

client_id = open("client_ID.txt",'r').read()
access_token = open("access_token.txt",'r').read()

fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="D:\FyiersApiAutomation\logs")

def fetchOHLC2(ticker,interval,duration):
    range_from = dt.date.today() - dt.timedelta(duration)
    range_to = dt.date.today()

    from_date_string = range_from.strftime("%Y-%m-%d")
    to_date_string = range_to.strftime("%Y-%m-%d")

    data = {
        "symbol":ticker,
        "resolution":interval,
        "date_format":"1",
        "range_from":from_date_string,
        "range_to":to_date_string,
        "cont_flag":"1"
    }
    
    response = fyers.history(data=data)['candles']

    # Create a Dataframe
    columns = ['Timestamp','Open','High','Low','Close','Volume']
    df = pd.DataFrame(response, columns=columns)

    # Convert Timestamp to datetime in UTC
    df['Timestamp2'] = pd.to_datetime(df['Timestamp'],unit='s').dt.tz_localize(pytz.utc)

    # Convert Timestamp to IST
    ist = pytz.timezone('Asia/Kolkata')
    df['Timestamp2'] = df['Timestamp2'].dt.tz_convert(ist)

    return (df)
    #return df[['Timestamp2', 'Open', 'High', 'Low', 'Close', 'Volume']]

def MACD(DF,a,b,c):
    """ function to calculate MACD
        typical values a(fast moving average) = 12 ema
                       b(slow moving average) = 26 ema
                       c(signal line ma window) = 9 ema """

    df = DF.copy()
    df['MA_FAST'] = df['Close'].ewm(span=a, min_periods=a).mean()
    df['MA_SLOW'] = df['Close'].ewm(span=b, min_periods=b).mean()
    df['MACD'] = df['MA_FAST'] - df['MA_SLOW']
    df['Signal'] = df['MACD'].ewm(span=c, min_periods=c).mean()
    df.dropna(inplace=True)
    return df

# Fetch OHLC data using the function
response_df = fetchOHLC2("NSE:NIFTY50-INDEX","30",30)
print(response_df)

macd_df = MACD(response_df,12,26,9)
print(macd_df)

# create a plot with two subplots 
fig, (ax1,ax2) = plt.subplots(2, 1, figsize=(10,8), sharex=True)

# Plot the Close price of the stock
ax1.plot(response_df.index, response_df['Close'], label='Close Price', color='blue')
ax1.set_ylabel('Close Price')
ax1.legend()

# Plot the MACD and Signal Line
ax2.plot(macd_df.index, macd_df['MACD'], label='MACD', color='orange')
ax2.plot(macd_df.index, macd_df['Signal'], label='Signal Line', color='green')
ax2.set_xlabel('Date')
ax2.set_ylabel('MACD')
ax2.legend()

plt.tight_layout()
plt.show()
