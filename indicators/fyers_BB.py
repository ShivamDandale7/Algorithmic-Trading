
import pandas as pd
from fyers_apiv3 import fyersModel
import datetime as dt
import pytz
import matplotlib.pyplot as plt
from typing import Tuple, Optional

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

def Bollinger_Bands(DF,period,multiplier):
    """
    Bollinger Bands Technical Indicator
    
    Bollinger Bands consist of:
    - Middle Band: (Simple Moving Average) = 20 sma
    - Upper Band: SMA + (Standard Deviation * multiplier)
    - Lower Band: SMA - (Standard Deviation * multiplier)
    """

    df = DF.copy()
    df['middle_band'] = df['Close'].rolling(window=period).mean()
    df['std'] = df['Close'].rolling(window=period).std()

    df['upper_band'] = df['middle_band'] + (df['std'] * multiplier)
    df['lower_band'] = df['middle_band'] - (df['std'] * multiplier)

    df['percent_b'] = (df['Close'] - df['lower_band']) / (df['upper_band'] - df['lower_band'])

    df['Bandwidth'] = (df['upper_band'] - df['lower_band']) / df['middle_band']
    df.dropna(inplace=True)
    return df

response_df = fetchOHLC2("NSE:NIFTY50-INDEX","5",5)
print(response_df)

bb_df = Bollinger_Bands(response_df,20,2.0)
print(bb_df)

df = pd.DataFrame(bb_df)
df['Timestamp2'] = pd.to_datetime(df['Timestamp2'])
df.set_index('Timestamp2',inplace=True)
print(df)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10,8), sharex=True)
        
# Main chart
ax1.plot(bb_df.index, bb_df['Close'], label='Price', color='black', linewidth=1.5)
ax1.plot(bb_df.index, bb_df['middle_band'], label='Middle Band (SMA)', color='blue', linewidth=1)
ax1.plot(bb_df.index, bb_df['upper_band'], label='Upper Band', color='red', linewidth=1)
ax1.plot(bb_df.index, bb_df['lower_band'], label='Lower Band', color='green', linewidth=1)

# Fill between bands
ax1.fill_between(bb_df.index, bb_df['upper_band'], bb_df['lower_band'], 
alpha=0.1, color='gray', label='Band Area')

ax1.set_title('Bollinger Band')
ax1.set_ylabel('Price')
ax1.legend()
ax1.grid(True, alpha=0.3)

# %B subplot
ax2.plot(bb_df.index, bb_df['percent_b'], label='%B', color='purple', linewidth=1)
ax2.axhline(y=0, color='green', linestyle='--', alpha=0.7, label='Lower Band')
ax2.axhline(y=1, color='red', linestyle='--', alpha=0.7, label='Upper Band')
ax2.axhline(y=0.5, color='blue', linestyle='--', alpha=0.7, label='Middle Band')
ax2.fill_between(bb_df.index, 0, 1, alpha=0.1, color='gray')

ax2.set_ylabel('%B')
ax2.set_xlabel('Date')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()