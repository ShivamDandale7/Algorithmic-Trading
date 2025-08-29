
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

    return (df)


def rsi(df, period):
    """
    Calculate the Relative Strength Index (RSI) for a DataFrame with closing price data.

    Parameters:
        df (pd.DataFrame): DataFrame containing OHLC (Open, High, Low, Close) data.
        period (int): Number of periods for RSI calculation (default: 14).

    Returns:
        pd.DataFrame: DataFrame with RSI values added as a new column.
    """
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    df['rsi'] = rsi
    return df


# Fetch OHLC data using the function
stock_df = fetchOHLC2("NSE:SBIN-EQ","30",100)
print(stock_df)

rsi_df = rsi(stock_df,14)
print(rsi_df)

fig = plt.figure(figsize = (10, 6))
ax1 = plt.subplot2grid((7, 1), (1, 0), rowspan = 3, colspan = 4)
ax1.plot(stock_df['Close'])
plt.subplots_adjust(top = 1.05, hspace = 0)

ax2 = plt.subplot2grid((7, 1), (4, 0), sharex = ax1, rowspan = 1, colspan = 4)
ax2.plot(rsi_df['rsi'], color = 'black')

ax2.axhline(70, color = 'red', linestyle = 'dotted', linewidth = 2)
ax2.axhline(30, color = 'green', linestyle = 'dotted', linewidth = 2)
ax2.set_yticks([30, 70])

#plt.tight_layout()
plt.show()


