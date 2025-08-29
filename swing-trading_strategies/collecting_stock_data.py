import numpy as np
import pandas as pd
from fyers_apiv3 import fyersModel
import pytz
import datetime as dt

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
    df['Date'] = pd.to_datetime(df['Timestamp'],unit='s').dt.tz_localize(pytz.utc)

    # Convert Timestamp to IST
    ist = pytz.timezone('Asia/Kolkata')
    df['Date'] = df['Date'].dt.tz_convert(ist)

    df = df.drop(columns=['Timestamp'])
    return df[['Date','Open','High','Low','Close']]


##################################################################################################################################
def filter_data_by_sma_blocks(data, sma_column='SMA_44', block_size=10):
    """
    Filters the dataframe by checking if SMA is rising within each block of size `block_size`.
    Keeps only the blocks where SMA[end] > SMA[start].
    """
    data = data.copy().reset_index(drop=True)
    filtered_blocks = []

    for i in range(0, len(data) - block_size + 1, block_size):
        block = data.iloc[i:i + block_size]
        sma_start = block.iloc[0][sma_column]
        sma_end = block.iloc[-1][sma_column]

        # If SMA is rising in this block, retain the block
        if pd.notna(sma_start) and pd.notna(sma_end) and sma_end > sma_start:
            filtered_blocks.append(block)

    # Combine all the kept blocks
    filtered_data = pd.concat(filtered_blocks, ignore_index=True)
    return filtered_data

###############################################################################################################################

def detect_double_bottom(data, window=10, depth=5):
    signals = []
    seen_dates = set()  # To track unique signal dates

    # Ensure index is datetime for proper date referencing
    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index)

    # Reset index for position-based referencing if needed
    data = data.reset_index()

    for i in range(window, len(data) - window):
        # First bottom
        first_bottom_idx = data['Low'][i - window:i].idxmin()
        first_bottom = data.loc[first_bottom_idx]

        # Second bottom
        second_bottom_idx = data['Low'][i:i + window].idxmin()
        second_bottom = data.loc[second_bottom_idx]

        # Neckline between two bottoms
        neckline = max(data.loc[first_bottom_idx:second_bottom_idx]['High'])

        # Check if both bottoms are near in price (within 2%)
        price_diff_pct = abs(first_bottom['Low'] - second_bottom['Low']) / first_bottom['Low'] * 100

        if price_diff_pct <= 2:
            try:
                buy_row = data.loc[second_bottom_idx + depth]
                signal_date = data.loc[second_bottom_idx + depth, 'Date']

                # Only add if this signal date hasn't been seen before
                if signal_date not in seen_dates:
                    seen_dates.add(signal_date)

                    signals.append({
                        'Signal_Date': signal_date,
                        'Buy_Price': buy_row['Close'],
                        'StopLoss': second_bottom['Low'],
                        'First_Bottom_Date': data.loc[first_bottom_idx, 'Date'],
                        'Second_Bottom_Date': data.loc[second_bottom_idx, 'Date'],
                        'Neckline': neckline
                    })

            except Exception as e:
                continue  # Skip if index out of range

    return pd.DataFrame(signals)

########################################################################################################################################

def run_scanner(symbols):
    results = []
    
    for symbol in symbols:
        df = fetchOHLC2(symbol,"D",100)
        if df.empty:
            continue
        
        # Calculate SMA(44)
        # Calculating Simple moving average

        df['SMA_44'] = df['Close'].rolling(window=44).mean().round(2)
        #df = df.dropna()
        last_close = df['Close'].iloc[-1]
        last_sma = df['SMA_44'].iloc[-1]
        
        # Condition 1: Uptrend
        uptrend_filtered_data = filter_data_by_sma_blocks(df)
        
        # Condition 2: Double Bottom
        signals = detect_double_bottom(uptrend_filtered_data)
        #print(signals)
        # signal_date = signals['Signal_Date'].iloc[-1]
        # Buy_price = signals['Buy_Price'].iloc[-1]

        results.append({
            "Symbol": symbol,
            "Last_Close": round(last_close,2),
            "SMA44": round(last_sma,2),
            "Signals": signals
        })
    
    #print(uptrend_filtered_data)
    return pd.DataFrame(results)

# ----------------------------
# Example Run
# ----------------------------
# symbols = ['NSE:SBIN-EQ','NSE:HDFCBANK-EQ','NSE:BHARTIARTL-EQ','NSE:ICICIBANK-EQ','NSE:HINDUNILVR-EQ',
#            'NSE:BAJFINANCE-EQ']  # replace with your stock list

#symbols = ['NSE:SBIN-EQ','NSE:HDFCBANK-EQ','NSE:ICICIBANK-EQ','NSE:BHARTIARTL-EQ','NSE:HINDUNILVR-EQ',
#           'NSE:BAJFINANCE-EQ','NSE:LAURUSLABS-EQ']

symbols = ['NSE:SBIN-EQ']
signals_df = run_scanner(symbols)
print(signals_df)