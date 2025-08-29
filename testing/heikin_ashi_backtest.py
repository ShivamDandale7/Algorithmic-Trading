import pandas as pd
import numpy as np

# Function to calculate Heikin-Ashi candles
def calculate_heikin_ashi(data):
    ha_data = data.copy()
    ha_data['HA_Close'] = (data['Open'] + data['High'] + data['Low'] + data['Close']) / 4
    ha_data['HA_Open'] = (data['Open'].shift(1) + data['Close'].shift(1)) / 2
    ha_data['HA_Open'].iloc[0] = (data['Open'].iloc[0] + data['Close'].iloc[0]) / 2

    for i in range(1, len(data)):
        ha_data['HA_Open'].iloc[i] = (ha_data['HA_Open'].iloc[i-1] + ha_data['HA_Close'].iloc[i-1]) / 2
    
    ha_data['HA_High'] = ha_data[['HA_Open', 'HA_Close', 'High']].max(axis=1)
    ha_data['HA_Low'] = ha_data[['HA_Open', 'HA_Close', 'Low']].min(axis=1)

    ha_data = ha_data.round(2)
    return ha_data


# Function to calculate Supertrend
import pandas as pd
import numpy as np


def calculate_atr_wilder(df, period):
    df = df.copy()
    df['H-L'] = df['HA_High'] - df['HA_Low']
    df['H-Cp'] = abs(df['HA_High'] - df['HA_Close'].shift(1))
    df['L-Cp'] = abs(df['HA_Low'] - df['HA_Close'].shift(1))
    df['TR'] = df[['H-L', 'H-Cp', 'L-Cp']].max(axis=1)

    atr = []
    tr_list = df['TR'].tolist()

    for i in range(len(tr_list)):
        if i < period:
            atr.append(np.nan)
        elif i == period:
            atr.append(np.mean(tr_list[1:period+1]))
        else:
            atr.append(((atr[i-1] * (period - 1)) + tr_list[i]) / period)

    df['ATR'] = atr
    df.drop(['H-L', 'H-Cp', 'L-Cp', 'TR'], axis=1, inplace=True)
    return df

def calculate_supertrend(df, atr_period, multiplier):
    df = calculate_atr_wilder(df, atr_period)
    hl2 = (df['HA_High'] + df['HA_Low']) / 2
    df['UpperBand'] = hl2 + (multiplier * df['ATR'])
    df['LowerBand'] = hl2 - (multiplier * df['ATR'])
    
    df['FinalUpperBand'] = df['UpperBand']
    df['FinalLowerBand'] = df['LowerBand']
    df['Supertrend'] = np.nan
    df['Trend'] = True  # True for bullish, False for bearish

    for i in range(atr_period + 1, len(df)):
        curr_close = df.loc[i, 'HA_Close']
        prev_close = df.loc[i-1, 'HA_Close']
        
        # Adjust final upper band
        if (df.loc[i, 'UpperBand'] < df.loc[i-1, 'FinalUpperBand']) or (prev_close > df.loc[i-1, 'FinalUpperBand']):
            df.loc[i, 'FinalUpperBand'] = df.loc[i, 'UpperBand']
        else:
            df.loc[i, 'FinalUpperBand'] = df.loc[i-1, 'FinalUpperBand']
        
        # Adjust final lower band
        if (df.loc[i, 'LowerBand'] > df.loc[i-1, 'FinalLowerBand']) or (prev_close < df.loc[i-1, 'FinalLowerBand']):
            df.loc[i, 'FinalLowerBand'] = df.loc[i, 'LowerBand']
        else:
            df.loc[i, 'FinalLowerBand'] = df.loc[i-1, 'FinalLowerBand']
        
        # Determine Supertrend
        if df.loc[i-1, 'Supertrend'] == df.loc[i-1, 'FinalUpperBand']:
            if curr_close <= df.loc[i, 'FinalUpperBand']:
                df.loc[i, 'Supertrend'] = df.loc[i, 'FinalUpperBand']
                df.loc[i, 'Trend'] = False
            else:
                df.loc[i, 'Supertrend'] = df.loc[i, 'FinalLowerBand']
                df.loc[i, 'Trend'] = True
        elif df.loc[i-1, 'Supertrend'] == df.loc[i-1, 'FinalLowerBand']:
            if curr_close >= df.loc[i, 'FinalLowerBand']:
                df.loc[i, 'Supertrend'] = df.loc[i, 'FinalLowerBand']
                df.loc[i, 'Trend'] = True
            else:
                df.loc[i, 'Supertrend'] = df.loc[i, 'FinalUpperBand']
                df.loc[i, 'Trend'] = False
        else:
            # Initialize
            df.loc[i, 'Supertrend'] = df.loc[i, 'FinalUpperBand']

    df['Supertrend'] = df['Supertrend'].round(2)
    return df['Supertrend']



# Function to generate buy/sell signals

def generate_signals(data, contraction_threshold_pct=0.5):
    """
    Generates trading signals based on the Dual Supertrend and Heikin-Ashi strategy.

    Parameters:
    - data (pd.DataFrame): DataFrame with columns ['Close', 'HA_Open', 'HA_Close', 
                                                   'Supertrend1', 'Supertrend2'].
    - contraction_threshold_pct (float): Max allowed % difference between Supertrends for entry.

    Returns:
    - pd.DataFrame: DataFrame with 'Signal' column added.
    """
    df = data.copy()

    # --- Rule 2: Calculate Supertrend Contraction ---
    supertrend_distance = abs(df['Supertrend1'] - df['Supertrend2'])
    contraction_pct = (supertrend_distance / (df['Close'] + 1e-8)) * 100
    is_contracted = contraction_pct < contraction_threshold_pct

    # --- Rule 1: Define Trend Conditions ---
    ha_is_bullish = df['HA_Close'] > df['HA_Open']
    ha_is_bearish = df['HA_Close'] < df['HA_Open']

    price_above_both_st = (df['Close'] > df['Supertrend1']) & (df['Close'] > df['Supertrend2'])
    price_below_both_st = (df['Close'] < df['Supertrend1']) & (df['Close'] < df['Supertrend2'])

    # --- Combine Rules for Entry Signals ---
    buy_call_condition = price_above_both_st & ha_is_bullish & is_contracted
    buy_put_condition = price_below_both_st & ha_is_bearish & is_contracted

    # --- Rule 3: Define Exit Conditions ---
    exit_call_condition = df['Close'] < df['Supertrend2']
    exit_put_condition = df['Close'] > df['Supertrend2']

    # --- Generate Final Signals ---
    df['Signal'] = ''
    position = 0  # 0: No position, 1: In Call, -1: In Put

    for i in range(1, len(df)):
        if position == 0:
            if buy_call_condition.iloc[i]:
                df.loc[i, 'Signal'] = 'BUY_CALL'
                position = 1
            elif buy_put_condition.iloc[i]:
                df.loc[i, 'Signal'] = 'BUY_PUT'
                position = -1

        elif position == 1:
            if exit_call_condition.iloc[i]:
                df.loc[i, 'Signal'] = 'EXIT'
                position = 0

        elif position == -1:
            if exit_put_condition.iloc[i]:
                df.loc[i, 'Signal'] = 'EXIT'
                position = 0

    return df


# Backtesting logic
def backtest_strategy(data):
    initial_balance = 100000  # Starting capital
    balance = initial_balance
    position = 0
    entry_price = 0
    trades = 0
    profit = 0

    for i in range(len(data)):
        if data['Signal'].iloc[i] == 'BUY_CALL' or data['Signal'].iloc[i] == 'BUY_PUT' and position == 0:
            # Enter a long position
            entry_price = data['Close'].iloc[i]
            position = 1
            trades += 1
        elif data['Signal'].iloc[i] == 'EXIT' and position == 1:
            # Exit the long position
            exit_price = data['Close'].iloc[i]
            profit += (exit_price - entry_price)
            balance += (exit_price - entry_price)
            position = 0

    # Calculate performance metrics
    total_profit = profit
    return_percentage = (balance - initial_balance) / initial_balance * 100
    win_rate = (profit / trades) if trades > 0 else 0

    # Print strategy summary
    print("Backtesting Summary:")
    print(f"Initial Balance: {initial_balance}")
    print(f"Final Balance: {balance}")
    print(f"Total Profit: {total_profit}")
    print(f"Return Percentage: {return_percentage:.2f}%")
    print(f"Total Trades: {trades}")
    print(f"Win Rate: {win_rate:.2f}")

# Main function
def main():
    # Load 5-minute candle data from CSV
    input_file = 'nifty50_5min.csv'  # Replace with your file path
    data = pd.read_csv(input_file)

    # Calculate Heikin-Ashi candles
    data = calculate_heikin_ashi(data)
    print(data)

    # Calculate Supertrend indicators
    data['Supertrend1'] = calculate_supertrend(data, atr_period=21, multiplier=1)
    data['Supertrend2'] = calculate_supertrend(data, atr_period=14, multiplier=2)

    # Generate buy/sell signals
    data = generate_signals(data)

    # Backtest the strategy
    backtest_strategy(data)

    # Save the output to a CSV file
    output_file = 'strategy_output_N50.csv'
    data.to_csv(output_file, index=False)
    print(f"Strategy output saved to {output_file}")

if __name__ == "__main__":
    main()