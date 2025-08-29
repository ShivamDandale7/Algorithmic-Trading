
import os
import datetime as dt
import pandas as pd
from fyers_apiv3 import fyersModel
import pytz


#generate trading session
client_id = open("client_ID.txt",'r').read()
access_token = open("access_token.txt",'r').read()

# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="D:\FyiersApiAutomation\logs")

def fetchOHLC_full(ticker,interval,inception_date):

    from_date = dt.datetime.strptime(inception_date, '%Y-%m-%d')
    to_date = dt.date.today()

    # Create a DataFrame
    columns = ['Timestamp','Open','High','Low','Close','Volume']
    df = pd.DataFrame(columns=columns)

    while True:
        from_date_string = from_date.strftime("%Y-%m-%d")
        ttoday = dt.date.today()
        to_date_string = ttoday.strftime("%Y-%m-%d")

        if from_date.date() >= (dt.date.today() - dt.timedelta(50)):
            data = {
                "symbol":ticker,
                "resolution":interval,
                "date_format":"1",
                "range_from":from_date_string,
                "range_to":to_date_string,
                "cont_flag":"1"
            }
            resp = fyers.history(data=data)['candles']
            df1 = pd.DataFrame(resp, columns=columns)
            result = pd.concat([df, df1], ignore_index=True)
            df = result
            break
        else:
            to_date = from_date + dt.timedelta(50)
            to_date_string = to_date.strftime("%Y-%m-%d")
            data = {
                "symbol":ticker,
                "resolution":interval,
                "date_format":"1",
                "range_from":from_date_string,
                "range_to":to_date_string,
                "cont_flag":"1"
            }
            resp = fyers.history(data=data)['candles']
            df1 = pd.DataFrame(resp, columns=columns)
            result = pd.concat([df, df1], ignore_index=True)
            df = result
            from_date = to_date + dt.timedelta(1)

    # Convert Timestamp to datetime in UTC
    df['Date'] = pd.to_datetime(df['Timestamp'],unit='s').dt.tz_localize(pytz.utc)

    # Convert Timestamp to IST
    ist = pytz.timezone('Asia/Kolkata')
    df['Date'] = df['Date'].dt.tz_convert(ist)

    #return df[['Date', 'Open', 'High', 'Low', 'Close']]
    return (df)

# Fetch OHLC data using the function
response_df = fetchOHLC_full("NSE:RELIANCE-EQ","D","2021-01-01")

# Print the DataFrame
print(response_df)

# Save data to a CSV file
response_df.to_csv('RELIANCE_1d_data_JAN2021-JULY2025.csv', index=False)


