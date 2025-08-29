
import datetime as dt
from fyers_apiv3 import fyersModel
import pandas as pd
import pytz

client_id = open("client_ID.txt",'r').read()
access_token = open("access_token.txt",'r').read()

fyers = fyersModel.FyersModel(client_id=client_id,token=access_token,is_async=False,log_path="D:\FyiersApiAutomation\logs")

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

    # Convert timestamp to datetime in UTC
    df['Timestamp2'] = pd.to_datetime(df['Timestamp'],unit='s').dt.tz_localize(pytz.utc)

    # convert timestamp to IST
    ist = pytz.timezone('Asia/Kolkata')
    df['Timestamp2'] = df['Timestamp2'].dt.tz_convert(ist)

    return(df)

def doji(ohlc_df):
    """ returns dataframe with doji candle data """
    df = ohlc_df.copy()

    """ Creating an array to store candle doji/not doji """
    doji_values = []

    """ Iter through rows and make comparison"""
    for index, row in df.iterrows():
        if abs(row['Open'] - row['Close']) <= 0.2*(row['High'] - row['Close']):
            doji_values.append(True)
        else:
            doji_values.append(False)
    
    df["Doji"] = doji_values

    return df

# Fetch OHLC data using the function
response_df = fetchOHLC2("NSE:NIFTY50-INDEX","30",50)
doji_df = doji(response_df)
print(doji_df)

doji_df.to_csv('output_doji.csv',index=False)

# daily_df = stock_df.resample('D').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'})
# daily_df.dropna(inplace=True)
# print(daily_df)


    