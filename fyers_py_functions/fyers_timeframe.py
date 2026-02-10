
import datetime as dt
from fyers_apiv3 import fyersModel
import pandas as pd
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

    return (df)


# Fetch OHLC data using the function
stock_df = fetchOHLC2("NSE:SBIN-EQ","1",20)
#print(stock_df)
stock_df['Timestamp2'] = pd.to_datetime(stock_df['Timestamp2'])
stock_df.drop(columns=['Timestamp'], inplace=True)
stock_df.set_index('Timestamp2', inplace=True)
print(stock_df)
#stock_df.to_csv('sbin_1min.csv')

min15_df = stock_df.resample('15T').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
min15_df.dropna(inplace=True)
print('15 MIN TIMEFRAME')
print(min15_df)

hourly_df = stock_df.resample('H').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
hourly_df.dropna(inplace=True)
print('HOURLY TIMEFRAME')
print(hourly_df)

daily_df = stock_df.resample('D').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
daily_df.dropna(inplace=True)
print('DAILY TIMEFRAME')
print(daily_df)

#HOURLY WITH 9:15
stock_df_2 = stock_df[stock_df.index.time <= pd.Timestamp('15:30').time()]
stock_df_2.index = stock_df_2.index - pd.Timedelta(minutes=15)
print(stock_df_2)
print("RUNNING TILL HERE")
hourly_df_2 = stock_df_2.resample('H').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
hourly_df_2.dropna(inplace=True)
hourly_df_2.index = hourly_df_2.index + pd.Timedelta(minutes=15)
print('HOURLY TIMEFRAME')
print(hourly_df_2)
