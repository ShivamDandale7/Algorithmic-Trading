
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

def pivotpoints_today(ohlc_day):
    """ returns pivot points and support/resistance levels"""
    high = round(ohlc_day["High"].iloc[-1],2)
    low = round(ohlc_day["Low"].iloc[-1],2)
    close = round(ohlc_day["Close"].iloc[-1],2)
    pivot = round((high + low + close)/3,2)
    r1 = round((2*pivot - low),2)
    r2 = round((pivot + (high - low)),2)
    r3 = round((high + 2*(pivot - low)),2)
    s1 = round((2*pivot - high),2)
    s2 = round((pivot - (high-low)),2)
    s3 = round((low - 2*(high - pivot)),2)
    return (pivot,r1,r2,r3,s1,s2,s3)


# Fetch OHLC data using the function
stock_df = fetchOHLC2("NSE:NIFTY50-INDEX","30",50)

stock_df['Timestamp2'] = pd.to_datetime(stock_df['Timestamp2'])
stock_df.drop(columns=['Timestamp'], inplace=True)
stock_df.set_index('Timestamp2', inplace=True)
print(stock_df)

daily_df = stock_df.resample('D').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'})
daily_df.dropna(inplace=True)
print(daily_df)

pivot,r1,r2,r3,s1,s2,s3 = pivotpoints_today(daily_df)
print("Pivot of today: ",pivot)
print("R1: ",r1)
print("R2: ",r2)
print("R3: ",r3)
print("S1: ",s1)
print("S2: ",s2)
print("S3: ",s3)

    