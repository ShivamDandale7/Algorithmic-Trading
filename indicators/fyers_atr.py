
import datetime as dt
from fyers_apiv3 import fyersModel
import pandas as pd
import pytz
import matplotlib.pyplot as plt

#generate trading session
client_id = open("client_ID.txt",'r').read()
access_token = open("access_token.txt",'r').read()

# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="D:\FyiersApiAutomation\logs")

def fetchOHLC2(ticker,interval,duration):
    range_from = dt.date.today()-dt.timedelta(duration)
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

    # Create a DataFrame
    columns = ['Timestamp','Open','High','Low','Close','Volume']
    df = pd.DataFrame(response, columns=columns)

    # Convert Timestamp to datetime in UTC
    df['Timestamp2'] = pd.to_datetime(df['Timestamp'],unit='s').dt.tz_localize(pytz.utc)

    # Convert Timestamp to IST
    ist = pytz.timezone('Asia/Kolkata')
    df['Timestamp2'] = df['Timestamp2'].dt.tz_convert(ist)
    df.drop(columns=['Timestamp'], inplace=True)

    return (df)


def atr(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['High-Low']=abs(df['High']-df['Low'])
    df['High-PrevClose']=abs(df['High']-df['Close'].shift(1))
    df['Low-PrevClose']=abs(df['Low']-df['Close'].shift(1))
    df['TR']=df[['High-Low','High-PrevClose','Low-PrevClose']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].ewm(com=n,min_periods=n).mean()
    df.dropna(inplace=True)
    return df


# Fetch OHLC data using the function
stock_df = fetchOHLC2("NSE:NIFTY50-INDEX","30",10)
print(stock_df)

atr_df = atr(stock_df,14)
print(atr_df)

fig = plt.figure(figsize = (10, 6))
ax1 = plt.subplot2grid((7, 1), (1, 0), rowspan = 3, colspan = 4)
ax1.plot(stock_df['Close'])
plt.subplots_adjust(top = 1.05, hspace = 0)

ax2 = plt.subplot2grid((7, 1), (4, 0), sharex = ax1, rowspan = 1, colspan = 4)
ax2.plot(atr_df['ATR'], color = 'black')

ax2.axhline(100, color = 'red', linestyle = 'dotted', linewidth = 2)
ax2.axhline(10, color = 'green', linestyle = 'dotted', linewidth = 2)
ax2.set_yticks([10, 100])

#plt.tight_layout()
plt.show()


