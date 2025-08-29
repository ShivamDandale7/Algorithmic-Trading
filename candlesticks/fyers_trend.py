
import pandas as pd
from fyers_apiv3 import fyersModel
import datetime as dt
import pytz
import numpy as np
import statsmodels.api as sm    #pip install statsmodels

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


def trend(df):
    trend = None

    i = len(df) -1
    # Uptrend condition
    if df['Close'][i] > df['Open'][i] and df['Close'][i-1] > df['Open'][i-1] and df['Close'][i-2] > df['Open'][i-2] and\
            df['High'][i] > df['High'][i - 1] and df['High'][i - 1] > df['High'][i - 2] and \
            df['Low'][i] > df['Low'][i - 1] and df['Low'][i - 1] > df['Low'][i - 2]:
        trend = 'Uptrend'

    # Downtrend condition
    elif df['Close'][i] < df['Open'][i] and df['Close'][i-1] < df['Open'][i-1] and df['Close'][i-2] < df['Open'][i-2] and\
            df['High'][i] < df['High'][i - 1] and df['High'][i - 1] < df['High'][i - 2] and\
            df['Low'][i] < df['Low'][i - 1] and df['Low'][i - 1] < df['Low'][i - 2] :
        trend = 'Downtrend'

    else:
        trend = None

    return trend

response_df = fetchOHLC2("NSE:SBIN-EQ","5",5)
trd = trend(response_df)
print("Trend :",trd)