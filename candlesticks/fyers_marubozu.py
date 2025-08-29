
import pandas as pd
from fyers_apiv3 import fyersModel
import datetime as dt
import pytz

#generate trading session
client_id = open("../FyiersApiAutomation/client_ID.txt",'r').read()
access_token = open("../FyiersApiAutomation/access_token.txt",'r').read()

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


def bullish_marubozu(ohlc_df, buffer=2):
    """Returns DataFrame with Bullish Marubozu candle column"""
    df = ohlc_df.copy()

    # Initialize an empty list to store the Bullish Marubozu values
    bullish_marubozu_values = []

    # Iterate through rows and perform the comparison
    for index, row in df.iterrows():
        if row["Close"] > row["Open"] and abs(row["High"] - row["Close"]) <= buffer and abs(row["Low"] - row["Open"]) <= buffer:
            bullish_marubozu_values.append(True)
        else:
            bullish_marubozu_values.append(False)

    # Create a new 'BullishMarubozu' column in the DataFrame
    df["BullishMarubozu"] = bullish_marubozu_values

    return df

def bearish_marubozu(ohlc_df, buffer=2):
    """Returns DataFrame with Bearish Marubozu candle column"""
    df = ohlc_df.copy()

    # Initialize an empty list to store the Bearish Marubozu values
    bearish_marubozu_values = []

    # Iterate through rows and perform the comparison
    for index, row in df.iterrows():
        if row["Open"] > row["Close"] and abs(row["High"] - row["Open"]) <= buffer and abs(row["Low"] - row["Close"]) <= buffer:
            bearish_marubozu_values.append(True)
        else:
            bearish_marubozu_values.append(False)

    # Create a new 'BearishMarubozu' column in the DataFrame
    df["BearishMarubozu"] = bearish_marubozu_values

    return df

response_df = fetchOHLC2("NSE:NIFTY50-INDEX","5",5)
marubozu_df = bullish_marubozu(response_df)
print(marubozu_df)
marubozu_df = bearish_marubozu(response_df)
print(marubozu_df)