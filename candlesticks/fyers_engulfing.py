
import pandas as pd
from fyers_apiv3 import fyersModel
import datetime as dt
import pytz


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


def bullish_engulfing(ohlc_df):
    """Returns DataFrame with Bullish Engulfing candle column"""
    df = ohlc_df.copy()

    # Initialize an empty list to store the Bullish Engulfing values
    bullish_engulfing_values = [False]

    # Iterate through rows and perform the comparison
    for i in range(1, len(df)):
        previous_row = df.iloc[i - 1]
        current_row = df.iloc[i]
        if (previous_row["Open"] > previous_row["Close"]) and \
                (current_row["Open"] < current_row["Close"]) and \
                (current_row["Open"] <= previous_row["Close"]) and \
                (current_row["Close"] >= previous_row["Open"]):
            bullish_engulfing_values.append(True)
        else:
            bullish_engulfing_values.append(False)

    # Create a new 'BullishEngulfing' column in the DataFrame
    df["BullishEngulfing"] = bullish_engulfing_values

    return df

def bearish_engulfing(ohlc_df):
    """Returns DataFrame with Bearish Engulfing candle column"""
    df = ohlc_df.copy()

    # Initialize an empty list to store the Bearish Engulfing values
    bearish_engulfing_values = [False]

    # Iterate through rows and perform the comparison
    for i in range(1, len(df)):
        previous_row = df.iloc[i - 1]
        current_row = df.iloc[i]
        if (previous_row["Open"] < previous_row["Close"]) and \
                (current_row["Open"] > current_row["Close"]) and \
                (current_row["Open"] >= previous_row["Close"]) and \
                (current_row["Close"] <= previous_row["Open"]):
            bearish_engulfing_values.append(True)
        else:
            bearish_engulfing_values.append(False)

    # Create a new 'BearishEngulfing' column in the DataFrame
    df["BearishEngulfing"] = bearish_engulfing_values

    return df

response_df = fetchOHLC2("NSE:NIFTY50-INDEX","30",5)
engulfing = bullish_engulfing(response_df)
print(engulfing[['Open', 'High', 'Low', 'Close', 'Timestamp2', 'BullishEngulfing']])
engulfing.to_csv('output_bullish_engulfing.csv',index=True)
engulfing = bearish_engulfing(response_df)
print(engulfing[['Open', 'High', 'Low', 'Close', 'Timestamp2', 'BearishEngulfing']])
engulfing.to_csv('output_bearish_engulfing.csv',index=True)