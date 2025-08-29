
import datetime as dt
import pandas as pd
import pytz
import mplfinance as mpf
import numpy as np


def atr(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['High-Low']=abs(df['High']-df['Low'])
    df['High-PrevClose']=abs(df['High']-df['Close'].shift(1))
    df['Low-PrevClose']=abs(df['Low']-df['Close'].shift(1))
    df['TR']=df[['High-Low','High-PrevClose','Low-PrevClose']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].ewm(com=n,min_periods=n).mean()
    return df['ATR']

def supertrend(DF,period=7,multiplier=3):
    df = DF.copy()
    df['ATR'] = atr(df,period)
    df["BasicUpper"]=((df['High']+df['Low'])/2) + multiplier*df['ATR']
    df["BasicLower"]=((df['High']+df['Low'])/2) - multiplier*df['ATR']
    df["FinalUpper"]=df["BasicUpper"]
    df["FinalLower"]=df["BasicLower"]
    ind = df.index
    for i in range(period,len(df)):
        if df['Close'][i-1]<=df['FinalUpper'][i-1]:
            df.loc[ind[i],'FinalUpper']=min(df['BasicUpper'][i],df['FinalUpper'][i-1])
        else:
            df.loc[ind[i],'FinalUpper']=df['BasicUpper'][i]
    for i in range(period,len(df)):
        if df['Close'][i-1]>=df['FinalLower'][i-1]:
            df.loc[ind[i],'FinalLower']=max(df['BasicLower'][i],df['FinalLower'][i-1])
        else:
            df.loc[ind[i],'FinalLower']=df['BasicLower'][i]
    df['Strend']=np.nan
    for test in range(period,len(df)):
        if df['Close'][test-1]<=df['FinalUpper'][test-1] and df['Close'][test]>df['FinalUpper'][test]:
            df.loc[ind[test],'Strend']=df['FinalLower'][test]
            break
        if df['Close'][test-1]>=df['FinalLower'][test-1] and df['Close'][test]<df['FinalLower'][test]:
            df.loc[ind[test],'Strend']=df['FinalUpper'][test]
            break
    for i in range(test+1,len(df)):
        if df['Strend'][i-1]==df['FinalUpper'][i-1] and df['Close'][i]<=df['FinalUpper'][i]:
            df.loc[ind[i],'Strend']=df['FinalUpper'][i]
        elif  df['Strend'][i-1]==df['FinalUpper'][i-1] and df['Close'][i]>=df['FinalUpper'][i]:
            df.loc[ind[i],'Strend']=df['FinalLower'][i]
        elif df['Strend'][i-1]==df['FinalLower'][i-1] and df['Close'][i]>=df['FinalLower'][i]:
            df.loc[ind[i],'Strend']=df['FinalLower'][i]
        elif df['Strend'][i-1]==df['FinalLower'][i-1] and df['Close'][i]<=df['FinalLower'][i]:
            df.loc[ind[i],'Strend']=df['FinalUpper'][i]
    return df


# Fetch OHLC data using the function
file_name = "nifty50_1d.csv"
stock_df = pd.read_csv(file_name, parse_dates=['Timestamp2'])
stock_df = stock_df.sort_values('Timestamp2')

supertrend_df = supertrend(stock_df,14,3)
print(supertrend_df[['FinalUpper','FinalLower','Strend']])

df = pd.DataFrame(supertrend_df)
df['Timestamp2'] = pd.to_datetime(df['Timestamp2'])
df.set_index('Timestamp2', inplace=True)

new_df = df.tail(250).copy()


# Create a plot with a candlestick chart and Bollinger Bands as lines
mpf.plot(new_df, type='candle', style='charles', title='Candlestick Chart with Supertrend',
         addplot=[
             mpf.make_addplot(new_df['Strend'], panel=0, color='orange', secondary_y=False),
         ])

