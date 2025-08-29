import pandas as pd
import datetime as dt 
from fyers_apiv3 import fyersModel
import pytz
import  matplotlib.pyplot as plt
import numpy as np

client_id = open("client_ID.txt",'r').read()
access_token = open("access_token.txt",'r').read()

fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="D:\FyiersApiAutomation\logs")

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

    # Convert Timestamp to datetime in UTC
    df['Timestamp2'] = pd.to_datetime(df['Timestamp'],unit='s').dt.tz_localize(pytz.utc)

    # Convert Timestamp to IST
    ist = pytz.timezone('Asia/Kolkata')
    df['Timestamp2'] = df['Timestamp2'].dt.tz_convert(ist)

    return (df)
    #return df[['Timestamp2', 'Open', 'High', 'Low', 'Close', 'Volume']]

def calculate_adx(DF,n):
    '''
Calculate the True Range (TR). True range is the Max of:
Current High minus Current Low
Current High minus Previous Close
Current Low minus Previous Close
Calculate the directional movement +DM1 and -DM1. Directional movement is positive  when the current high minus the previous high is greater than the previous low minus the current low. This so-called Plus Directional Movement (+DM) then equals the current high minus the prior high, provided it is positive. A negative value would simply be entered as zero. Directional movement is negative (minus) when the previous low minus the current low is greater than the current high minus the previous high. This so-called Minus Directional Movement (-DM) equals the prior low minus the current low, provided it is positive. A negative value would simply be entered as zero.
Calculate 14 period moving average of True range (TR14). Here the period 14 corresponds to the ADX period 14.
Calculate 14 period moving average of +DM1 and -DM1. It would be called +DM14 and -DM14.
Calculate +DI14 and -DI14.
+DI14 is the ratio of +DM14 and TR14 expressed in % terms.
-DI14 is the ratio of -DM14 and TR14 expressed in % terms.
Calculate Directional Movement Index (DX). It equals the absolute value of +DI14 minus -DI14 divided by the sum of +DI14 and – DI14. It is also expressed in % terms.
Calculate Average directional index (ADX). It is the 14 period moving average of DX.
'''

    df2 = DF.copy()
    df2['High-Low'] = abs(df2['High'] - df2['Low'])
    df2['High-PrevClose'] = abs(df2['High'] - df2['Close'].shift(1))
    df2['Low-PrevClose'] = abs(df2['Low'] - df2['Close'].shift(1))
    df2['TR'] = df2[['High-Low', 'High-PrevClose','Low-PrevClose']].max(axis=1,skipna=False)
    df2['DMplus'] = np.where((df2['High']-df2['High'].shift(1))>(df2['Low'].shift(1)-df2['Low']),df2['High']-df2['High'].shift(1),0)
    df2['DMplus'] = np.where(df2['DMplus']<0,0,df2['DMplus'])
    df2['DMminus'] = np.where((df2['Low'].shift(1)-df2['Low'])>(df2['High']-df2['High'].shift(1)),df2['Low'].shift(1)-df2['Low'],0)
    df2['DMminus'] = np.where(df2['DMminus']<0,0,df2['DMminus'])
    TRn = []
    DMplusN = []
    DMminusN = []
    TR = df2['TR'].tolist()
    DMplus = df2['DMplus'].tolist()
    DMminus = df2['DMminus'].tolist()
    for i in range(len(df2)):
        if i<n:
            TRn.append(np.NaN)
            DMplusN.append(np.NaN)
            DMminusN.append(np.NaN)

        elif i==n:
            TRn.append(df2['TR'].rolling(n).sum().tolist()[n])
            DMplusN.append(df2['DMplus'].rolling(n).sum().tolist()[n])
            DMminusN.append(df2['DMminus'].rolling(n).sum().tolist()[n])

        elif i>n:
            TRn.append(TRn[i-1] - (TRn[i-1]/n) + TR[i])
            DMplusN.append(DMplusN[i-1] - (DMplusN[i-1]/n) - DMplus[i])
            DMminusN.append((DMminusN[i-1]-DMminusN[i-1]/n) - DMminus[i])

    df2['TRn'] = np.array(TRn)
    df2['DMplusN'] = np.array(DMplusN)
    df2['DMminusN'] = np.array(DMminusN)
    df2['DIplusN'] = 100*(df2['DMplusN']/df2['TRn'])
    df2['DIminusN'] = 100*(df2['DMminusN']/df2['TRn'])
    df2['DIdiff'] = abs(df2['DIplusN'] - df2['DIminusN'])
    df2['DIsum'] = abs(df2['DIplusN'] + df2['DIminusN'])
    df2['DX'] = 100*(df2['DIdiff']/df2['DIsum'])
    ADX = []
    DX = df2['DX'].tolist()
    for j in range(len(df2)):
        if j < 2*n-1:
            ADX.append(np.NaN)
        elif j == 2*n-1:
            ADX.append(df2['DX'][j-n+1:j+1].mean())
        elif j > 2*n-1:
            ADX.append(((n-1)*ADX[j-1] + DX[j])/n)
    
    df2['ADX'] = np.array(ADX)
    return df2


# Fetch OHLC data using the function
response_df = fetchOHLC2("NSE:NIFTY50-INDEX","1D",100)
print(response_df)

adx_df = calculate_adx(response_df,14)
print(adx_df)

fig = plt.figure(figsize = (10, 6))
ax1 = plt.subplot2grid((7, 1), (1, 0), rowspan = 3, colspan = 4)
ax1.plot(response_df['Close'])
plt.subplots_adjust(top = 1.05, hspace = 0)

ax2 = plt.subplot2grid((7, 1), (4, 0), sharex = ax1, rowspan = 1, colspan = 4)
ax2.plot(adx_df['ADX'], color = 'black')

ax2.axhline(40, color = 'red', linestyle = 'dotted', linewidth = 2)
ax2.axhline(20, color = 'green', linestyle = 'dotted', linewidth = 2)
ax2.set_yticks([20, 40])

#plt.tight_layout()
plt.show()

