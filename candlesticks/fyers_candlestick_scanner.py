
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


def doji(ohlc_df):
    """returns dataframe with doji candle column"""
    df = ohlc_df.copy()

    # Initialize an empty list to store the Doji values
    doji_values = []

    # Iterate through rows and perform the comparison
    for index, row in df.iterrows():
        #print("index" , index)
        #print("row ", row)
        if abs(row["Open"] - row["Close"]) <= 0.1 * (row['High'] - row['Low']):
            doji_values.append(True)
        else:
            doji_values.append(False)

    # Create a new 'doji' column in the DataFrame
    df["Doji"] = doji_values

    return df

def bullish_marubozu(ohlc_df, buffer=0.05):
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

def bearish_marubozu(ohlc_df, buffer=0.05):
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

def hammer(ohlc_df):
    """
    In this function, we're checking two conditions to identify Hammer patterns:
    one for when the candle's body is at the top of the range, and the other for
    when it's at the bottom of the range. The conditions are based on the
    characteristics of a Hammer candlestick pattern.
    """
    df = ohlc_df.copy()

    # Initialize an empty list to store the Hammer values
    hammer_values = []

    # Iterate through rows and perform the comparison
    for index, row in df.iterrows():
        if (row["Open"] - row["Close"] > 0) and (row["Open"] - row["Low"] >= 2 * (row["High"] - row["Close"])):
            hammer_values.append(True)
        elif (row["Close"] - row["Open"] > 0) and (row["Close"] - row["Low"] >= 2 * (row["High"] - row["Open"])):
            hammer_values.append(True)
        else:
            hammer_values.append(False)

    # Create a new 'Hammer' column in the DataFrame
    df["Hammer"] = hammer_values

    return df

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
                (current_row["Open"] <= previous_row["Open"]) and \
                (current_row["Close"] >= previous_row["Close"]):
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
                (current_row["Open"] >= previous_row["Open"]) and \
                (current_row["Close"] <= previous_row["Close"]):
            bearish_engulfing_values.append(True)
        else:
            bearish_engulfing_values.append(False)

    # Create a new 'BearishEngulfing' column in the DataFrame
    df["BearishEngulfing"] = bearish_engulfing_values

    return df

def pivotpoints_today(ohlc_day):
    """returns pivot point and support/resistance levels"""
    high = round(ohlc_day["High"].iloc[-2],2)
    low = round(ohlc_day["Low"].iloc[-2],2)
    close = round(ohlc_day["Close"].iloc[-2],2)
    pivot = round((high + low + close)/3,2)
    r1 = round((2*pivot - low),2)
    r2 = round((pivot + (high - low)),2)
    r3 = round((high + 2*(pivot - low)),2)
    s1 = round((2*pivot - high),2)
    s2 = round((pivot - (high - low)),2)
    s3 = round((low - 2*(high - pivot)),2)
    return (pivot,r1,r2,r3,s1,s2,s3)

def trend(ohlc_df,n):
    "function to assess the trend by analyzing each candle"
    df = ohlc_df.copy()
    df["up"] = np.where(df["Low"]>=df["Low"].shift(1),1,0)
    df["dn"] = np.where(df["High"]<=df["High"].shift(1),1,0)
    if df["Close"].iloc[-1] > df["Open"].iloc[-1]:
        if df["up"][-1*n:].sum() >= 0.7*n:
            return "uptrend"
    elif df["Open"].iloc[-1] > df["Close"].iloc[-1]:
        if df["dn"][-1*n:].sum() >= 0.7*n:
            return "downtrend"
    else:
        return None
   
def res_sup(ohlc_df,ohlc_day):
    """calculates closest resistance and support levels for a given candle"""
    level = ohlc_df["Close"].iloc[-1]
    p,r1,r2,r3,s1,s2,s3 = pivotpoints_today(ohlc_day)

    # Create a list of variables and their values
    variables = {'p': p, 'r1': r1, 'r2': r2, 'r3': r3, 's1': s1, 's2': s2, 's3': s3}

    # Initialize variables to store the closest values above and below level
    closest_above_value = float('inf')
    closest_below_value = float('-inf')
    closest_above_variable = None
    closest_below_variable = None

    # Find the closest variables above and below level
    for variable, value in variables.items():
        difference = value - level
        if difference > 0 and difference < closest_above_value:
            closest_above_value = difference
            closest_above_variable = variable
        elif difference < 0 and abs(difference) < abs(closest_below_value):
            closest_below_value = difference
            closest_below_variable = variable

    return(variables[closest_above_variable], variables[closest_below_variable])

def candle_type(ohlc_df):    
    """returns the candle type of the last candle of an OHLC DF"""
    candle = None

    if doji(ohlc_df)["Doji"].iloc[-1] == True:
        candle = "doji"    
    if bullish_marubozu(ohlc_df)["BullishMarubozu"].iloc[-1] == True:
        candle = "marubozu_bull"
    if bearish_marubozu(ohlc_df)["BearishMarubozu"].iloc[-1] == True:
        candle = "marubozu_bear"
    if bullish_engulfing(ohlc_df)["BullishEngulfing"].iloc[-1] == True:
        candle = "engulfing_bull"
    if bearish_engulfing(ohlc_df)["BearishEngulfing"].iloc[-1] == True:
        candle = "engulfing_bear"
    if shooting_star(ohlc_df)["ShootingStar"].iloc[-1] == True:
        candle = "shooting_star"        
    if hammer(ohlc_df)["Hammer"].iloc[-1] == True:
        candle = "hammer"       
    return candle

def candle_pattern(ohlc_df,ohlc_day,n=7):
    """returns the candle pattern identified"""
    pattern = None
    momentum = None

    #For momentum we can see pivot points. If above pivot, then bullish, otherwise bearish
    sup, res = res_sup(ohlc_df,ohlc_day)
    pivot,r1,r2,r3,s1,s2,s3 = pivotpoints_today(ohlc_day)
    if trend(ohlc_df.iloc[:-1,:],n) == "uptrend" and ohlc_df["Close"].iloc[-1] > pivot:
        momentum = "bull"
    elif trend(ohlc_df.iloc[:-1,:],n) == "downtrend" and ohlc_df["Close"].iloc[-1] < pivot:
        momentum = "bear"


    #use trend and candle type
    if trend(ohlc_df.iloc[:-1,:],n) == "uptrend" and candle_type(ohlc_df) == "doji":
        pattern = "doji_bear"

    elif trend(ohlc_df.iloc[:-1,:],n) == "downtrend" and candle_type(ohlc_df) == "doji":
        pattern = "doji_bull"
            
    elif candle_type(ohlc_df) == "marubozu_bull":
        pattern = "marubozu_bull"
    
    elif candle_type(ohlc_df) == "marubozu_bear":
        pattern = "marubozu_bear"
        
    elif trend(ohlc_df.iloc[:-1,:],n) == "uptrend" and candle_type(ohlc_df) == "hammer":
        pattern = "hammer_bear"  #also called hanging man
        
    elif trend(ohlc_df.iloc[:-1,:],n) == "downtrend" and candle_type(ohlc_df) == "hammer":
        pattern = "hammer_bull"
        
    elif trend(ohlc_df.iloc[:-1,:],n) == "uptrend" and candle_type(ohlc_df) == "shooting_star":
        pattern = "shooting_star_bear"
        
    elif trend(ohlc_df.iloc[:-1,:],n) == "downtrend" and candle_type(ohlc_df) == "engulfing_bull":
        pattern = "engulfing_bull"

    elif trend(ohlc_df.iloc[:-1,:],n) == "uptrend" and candle_type(ohlc_df) == "engulfing_bear":
        pattern = "engulfing_bear"

    return(pattern, momentum)

##############################################################################################
tickers = ['NSE:ABB-EQ','NSE:ACC-EQ','NSE:ABBOTINDIA-EQ','NSE:ADANIENSOL-EQ',
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



def main():
    for ticker in tickers:
        try:
            ohlc = fetchOHLC2(ticker, '5',5)
            ohlc_day = fetchOHLC2(ticker, 'D',30)
            pattern, momentum = candle_pattern(ohlc,ohlc_day,7)
            print("Ticker: ", ticker, ": Pattern: ", pattern, " and Momentum: ",momentum)
            #time.sleep(1)
        except:
            print(ticker, ": Skipped")

    time.sleep(300)

main()