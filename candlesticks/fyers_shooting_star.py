
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


def shooting_star(ohlc_df):
    """In this function, we're checking two conditions to identify Shooting Star patterns:
    one for when the candle's body is at the bottom of the range,
    and the other for when it's at the top of the range. """
    df = ohlc_df.copy()

    # Initialize an empty list to store the Shooting Star values
    shooting_star_values = []

    # Iterate through rows and perform the comparison
    for index, row in df.iterrows():
        if (row["Open"] - row["Close"] > 0) and (row["High"] - row["Open"] >= 2 * (row["Close"] - row["Low"])):
            shooting_star_values.append(True)
        elif (row["Close"] - row["Open"] > 0) and (row["High"] - row["Close"] >= 2 * (row["Open"] - row["Low"])):
            shooting_star_values.append(True)
        else:
            shooting_star_values.append(False)

    # Create a new 'ShootingStar' column in the DataFrame
    df["ShootingStar"] = shooting_star_values

    return df

response_df = fetchOHLC2("NSE:NIFTY50-INDEX","30",5)
shootingstar_df = shooting_star(response_df)
print(shootingstar_df)