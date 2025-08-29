
import pandas as pd
from fyers_apiv3 import fyersModel
import datetime as dt
import pytz
import numpy as np
import time

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
    return df['Strend']


def rsi(df, period):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    df['rsi'] = rsi
    return df['rsi']

def placeOrder(inst ,t_type,qty,order_type,price=0, price_stop=0):
    exch = inst[:3]
    symb = inst[4:]
    if(order_type=="MARKET"):
        type1 = 2
        price = 0
        price_stop = 0
    elif(order_type=="LIMIT"):
        type1 = 1
        price_stop = 0
    elif(order_type=="SL-LIMIT"):
        type1 = 4

    if(t_type=="BUY"):
        side1=1
    elif(t_type=="SELL"):
        side1=-1

    data =  {
        "symbol":inst,
        "qty":qty,
        "type":type1,
        "side":side1,
        "productType":"INTRADAY",
        "limitPrice":price,
        "stopPrice":price_stop,
        "validity":"DAY",
    }

    try:
        orderid = fyers.place_order(data)
        print(symb , orderid)
        return orderid
    except Exception as e:
        print(symb , "Failed : {} ".format(e))


def main(capital):
    #initialise the indicator
    for ticker in tickers:
        print("Checking for: ",ticker)
        try:
            ohlc = fetchOHLC2(ticker,"5",5)
            ohlc["st1"] = supertrend(ohlc,7,3)
            ohlc['rsi'] = rsi(ohlc,14)
            quantity = int(capital/ohlc["Close"].iloc[-1])
            quantity = round(quantity,0)
            print(quantity)

            #Check if BUY Stoploss is hit or supertrend changes
            if (indicator_dir[ticker][0] == "BUY") and ((ohlc['Low'].iloc[-1] < indicator_dir[ticker][2]) or ohlc['st1'].iloc[-1] > ohlc['Close'].iloc[-1]):
                print(ticker, " BUY stoploss is hit")
                oid = placeOrder(ticker ,"SELL",quantity,"MARKET",price=0, price_stop=0)
                indicator_dir[ticker][0] = 0
                indicator_dir[ticker][1] = 0
                indicator_dir[ticker][2] = 0

            #check if SELL stoploss is hit or supertrend changes
            elif (indicator_dir[ticker][0] == "SELL") and ((ohlc['High'].iloc[-1] > indicator_dir[ticker][2]) or ohlc['st1'].iloc[-1] < ohlc['Close'].iloc[-1]):
                print(ticker, " SELL stoploss is hit")
                oid = placeOrder(ticker ,"BUY",quantity,"MARKET",price=0, price_stop=0)
                indicator_dir[ticker][0] = 0
                indicator_dir[ticker][1] = 0
                indicator_dir[ticker][2] = 0

            #BUY to be taken if st1 is green, rsi > 20 and either in no trade or SELL trade
            if (ohlc['st1'].iloc[-1] < ohlc['Close'].iloc[-1]) and (ohlc['rsi'].iloc[-1] > 20) and (indicator_dir[ticker][0] == 0):
                print(ticker, " Take BUY trade")
                oid = placeOrder(ticker ,"BUY",quantity,"MARKET",price=0, price_stop=0)
                indicator_dir[ticker][0] = "BUY"
                indicator_dir[ticker][1] = ohlc['Close'].iloc[-1]
                stoploss = ohlc['Close'].iloc[-1] * (1-0.005)
                indicator_dir[ticker][2] = stoploss

            #SELL to be taken if st1 is red, rsi < 70 and either in no trade or BUY trade
            elif (ohlc['st1'].iloc[-1] > ohlc['Close'].iloc[-1]) and (ohlc['rsi'].iloc[-1] < 70) and (indicator_dir[ticker][0] == 0):
                print(ticker, " Take SELL trade")
                oid = placeOrder(ticker ,"SELL",quantity,"MARKET",price=0, price_stop=0)
                indicator_dir[ticker][0] = "SELL"
                indicator_dir[ticker][1] = ohlc['Close'].iloc[-1]
                stoploss = ohlc['Close'].iloc[-1] * (1+0.005)
                indicator_dir[ticker][2] = stoploss



        except:
            print("API error for ticker :",ticker)

    time.sleep(300)


#############################################################################################################
tickers = ['NSE:ABB-EQ','NSE:ACC-EQ','NSE:AUBANK-EQ','NSE:ABBOTINDIA-EQ','NSE:ADANIENSOL-EQ',
           'NSE:ADANIENT-EQ','NSE:ADANIGREEN-EQ','NSE:ADANIPORTS-EQ','NSE:ADANIPOWER-EQ',
           'NSE:ATGL-EQ','NSE:AWL-EQ','NSE:ABCAPITAL-EQ','NSE:ABFRL-EQ','NSE:ALKEM-EQ',
           'NSE:AMBUJACEM-EQ','NSE:APOLLOHOSP-EQ','NSE:APOLLOTYRE-EQ','NSE:ASHOKLEY-EQ',
           'NSE:ASIANPAINT-EQ','NSE:ASTRAL-EQ','NSE:AUROPHARMA-EQ','NSE:DMART-EQ',
           'NSE:AXISBANK-EQ','NSE:BAJAJ-AUTO-EQ','NSE:BAJFINANCE-EQ','NSE:BAJAJFINSV-EQ',
           'NSE:BAJAJHLDNG-EQ','NSE:BALKRISIND-EQ','NSE:BANDHANBNK-EQ','NSE:BANKBARODA-EQ',
           'NSE:BANKINDIA-EQ','NSE:BATAINDIA-EQ','NSE:BERGEPAINT-EQ','NSE:BEL-EQ',
           'NSE:BHARATFORG-EQ','NSE:BHEL-EQ','NSE:BPCL-EQ','NSE:BHARTIARTL-EQ','NSE:BIOCON-EQ',
           'NSE:BOSCHLTD-EQ','NSE:BRITANNIA-EQ','NSE:CGPOWER-EQ','NSE:CANBK-EQ',
           'NSE:CHOLAFIN-EQ','NSE:CIPLA-EQ','NSE:COALINDIA-EQ','NSE:COFORGE-EQ',
           'NSE:COLPAL-EQ','NSE:CONCOR-EQ','NSE:COROMANDEL-EQ','NSE:CROMPTON-EQ',
           'NSE:CUMMINSIND-EQ','NSE:DLF-EQ','NSE:DABUR-EQ','NSE:DALBHARAT-EQ',
           'NSE:DEEPAKNTR-EQ','NSE:DELHIVERY-EQ','NSE:DEVYANI-EQ','NSE:DIVISLAB-EQ',
           'NSE:DIXON-EQ','NSE:LALPATHLAB-EQ','NSE:DRREDDY-EQ','NSE:EICHERMOT-EQ',
           'NSE:ESCORTS-EQ','NSE:NYKAA-EQ','NSE:FEDERALBNK-EQ','NSE:FORTIS-EQ',
           'NSE:GAIL-EQ','NSE:GLAND-EQ','NSE:GODREJCP-EQ','NSE:GODREJPROP-EQ','NSE:GRASIM-EQ',
           'NSE:FLUOROCHEM-EQ','NSE:GUJGASLTD-EQ','NSE:HCLTECH-EQ','NSE:HDFCAMC-EQ',
           'NSE:HDFCBANK-EQ','NSE:HDFCLIFE-EQ','NSE:HAVELLS-EQ','NSE:HEROMOTOCO-EQ',
           'NSE:HINDALCO-EQ','NSE:HAL-EQ','NSE:HINDPETRO-EQ','NSE:HINDUNILVR-EQ',
           'NSE:HINDZINC-EQ','NSE:HONAUT-EQ','NSE:ICICIBANK-EQ','NSE:ICICIGI-EQ',
           'NSE:ICICIPRULI-EQ','NSE:IDFCFIRSTB-EQ','NSE:ITC-EQ','NSE:INDIANB-EQ',
           'NSE:INDHOTEL-EQ','NSE:IOC-EQ','NSE:IRCTC-EQ','NSE:IRFC-EQ','NSE:IGL-EQ',
           'NSE:INDUSTOWER-EQ','NSE:INDUSINDBK-EQ','NSE:NAUKRI-EQ','NSE:INFY-EQ','NSE:INDIGO-EQ',
           'NSE:IPCALAB-EQ','NSE:JSWENERGY-EQ','NSE:JSWSTEEL-EQ','NSE:JINDALSTEL-EQ',
           'NSE:JIOFIN-EQ','NSE:JUBLFOOD-EQ','NSE:KOTAKBANK-EQ','NSE:L&TFH-EQ','NSE:LTTS-EQ',
           'NSE:LICHSGFIN-EQ','NSE:LTIM-EQ','NSE:LT-EQ','NSE:LAURUSLABS-EQ','NSE:LICI-EQ',
           'NSE:LUPIN-EQ','NSE:MRF-EQ','NSE:M&MFIN-EQ','NSE:M&M-EQ','NSE:MANKIND-EQ',
           'NSE:MARICO-EQ','NSE:MARUTI-EQ','NSE:MFSL-EQ','NSE:MAXHEALTH-EQ','NSE:MSUMI-EQ',
           'NSE:MPHASIS-EQ','NSE:MUTHOOTFIN-EQ','NSE:NHPC-EQ','NSE:NMDC-EQ','NSE:NTPC-EQ',
           'NSE:NAVINFLUOR-EQ','NSE:NESTLEIND-EQ','NSE:OBEROIRLTY-EQ','NSE:ONGC-EQ',
           'NSE:OIL-EQ','NSE:PAYTM-EQ','NSE:OFSS-EQ','NSE:POLICYBZR-EQ','NSE:PIIND-EQ',
           'NSE:PAGEIND-EQ','NSE:PATANJALI-EQ','NSE:PERSISTENT-EQ','NSE:PETRONET-EQ',
           'NSE:PIDILITIND-EQ','NSE:PEL-EQ','NSE:POLYCAB-EQ','NSE:POONAWALLA-EQ',
           'NSE:PFC-EQ','NSE:POWERGRID-EQ','NSE:PRESTIGE-EQ','NSE:PGHH-EQ','NSE:PNB-EQ',
           'NSE:RECLTD-EQ','NSE:RELIANCE-EQ','NSE:SBICARD-EQ','NSE:SBILIFE-EQ','NSE:SRF-EQ',
           'NSE:MOTHERSON-EQ','NSE:SHREECEM-EQ','NSE:SHRIRAMFIN-EQ','NSE:SIEMENS-EQ',
           'NSE:SONACOMS-EQ','NSE:SBIN-EQ','NSE:SAIL-EQ','NSE:SUNPHARMA-EQ','NSE:SUNTV-EQ',
           'NSE:SYNGENE-EQ','NSE:TVSMOTOR-EQ','NSE:TATACHEM-EQ','NSE:TATACOMM-EQ',
           'NSE:TCS-EQ','NSE:TATACONSUM-EQ','NSE:TATAELXSI-EQ','NSE:TATAMOTORS-EQ',
           'NSE:TATAPOWER-EQ','NSE:TATASTEEL-EQ','NSE:TTML-EQ','NSE:TECHM-EQ',
           'NSE:RAMCOCEM-EQ','NSE:TITAN-EQ','NSE:TORNTPHARM-EQ','NSE:TORNTPOWER-EQ',
           'NSE:TRENT-EQ','NSE:TRIDENT-EQ','NSE:TIINDIA-EQ','NSE:UPL-EQ','NSE:ULTRACEMCO-EQ',
           'NSE:UNIONBANK-EQ','NSE:UBL-EQ','NSE:MCDOWELL-N-EQ','NSE:VBL-EQ','NSE:VEDL-EQ',
           'NSE:IDEA-EQ','NSE:VOLTAS-EQ','NSE:WHIRLPOOL-EQ','NSE:WIPRO-EQ','NSE:YESBANK-EQ',
           'NSE:ZEEL-EQ','NSE:ZOMATO-EQ','NSE:ZYDUSLIFE-EQ']

capital = 5000 #position size
indicator_dir = {} #directory to store super trend status for each ticker

for ticker in tickers:
    indicator_dir[ticker] = [0,0,0]  #(1 current trade) 0/BUY/SELL # (2 entry price)  # (3 sl price) 0.5% of entry price

main(capital)
