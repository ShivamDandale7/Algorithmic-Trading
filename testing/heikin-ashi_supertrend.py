import pandas as pd
import numpy as np

def read_data(file_path):
    df = pd.read_csv(file_path)
    df.columns = [col.strip().capitalize() for col in df.columns]
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df.sort_values('Timestamp', inplace=True)
    return df

def heikin_ashi(df):
    ha_df = df.copy()
    ha_df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    ha_df['HA_Open'] = 0.0
    ha_df['HA_High'] = 0.0
    ha_df['HA_Low'] = 0.0

    for i in range(len(df)):
        if i == 0:
            ha_df.iloc[i, ha_df.columns.get_loc('HA_Open')] = (df['Open'].iloc[0] + df['Close'].iloc[0]) / 2
        else:
            ha_df.iloc[i, ha_df.columns.get_loc('HA_Open')] = (ha_df['HA_Open'].iloc[i-1] + ha_df['HA_Close'].iloc[i-1]) / 2

        ha_df.iloc[i, ha_df.columns.get_loc('HA_High')] = max(df['High'].iloc[i], ha_df['HA_Open'].iloc[i], ha_df['HA_Close'].iloc[i])
        ha_df.iloc[i, ha_df.columns.get_loc('HA_Low')] = min(df['Low'].iloc[i], ha_df['HA_Open'].iloc[i], ha_df['HA_Close'].iloc[i])
    
    return ha_df

def calculate_atr(df, period):
    df['H-L'] = df['HA_High'] - df['HA_Low']
    df['H-PC'] = np.abs(df['HA_High'] - df['HA_Close'].shift())
    df['L-PC'] = np.abs(df['HA_Low'] - df['HA_Close'].shift())
    tr = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_supertrend(df, period, multiplier):
    atr = calculate_atr(df, period)
    hl2 = (df['HA_High'] + df['HA_Low']) / 2
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)

    supertrend = [np.nan] * len(df)
    direction = [True] * len(df)  # True = uptrend, False = downtrend

    for i in range(period, len(df)):
        if df['HA_Close'].iloc[i] > upperband.iloc[i - 1]:
            direction[i] = True
        elif df['HA_Close'].iloc[i] < lowerband.iloc[i - 1]:
            direction[i] = False
        else:
            direction[i] = direction[i - 1]
            if direction[i] and lowerband.iloc[i] < lowerband.iloc[i - 1]:
                lowerband.iloc[i] = lowerband.iloc[i - 1]
            if not direction[i] and upperband.iloc[i] > upperband.iloc[i - 1]:
                upperband.iloc[i] = upperband.iloc[i - 1]

        supertrend[i] = lowerband.iloc[i] if direction[i] else upperband.iloc[i]

    df[f'Supertrend_{period}_{multiplier}'] = supertrend
    df[f'Direction_{period}_{multiplier}'] = direction
    return df

def generate_signals(df):
    conditions = (
        (df['Direction_14_2'] == True) & (df['Direction_21_1'] == True)
    )
    df['Signal'] = np.where(conditions, 'B', 'S')
    return df

def process(file_path, output_path):
    df = read_data(file_path)
    ha_df = heikin_ashi(df)
    ha_df = calculate_supertrend(ha_df, 14, 2)
    ha_df = calculate_supertrend(ha_df, 21, 1)
    ha_df = generate_signals(ha_df)
    
    output_df = ha_df[['Timestamp', 'HA_Open', 'HA_High', 'HA_Low', 'HA_Close', 
                       'Supertrend_14_2', 'Supertrend_21_1', 'Signal']]
    output_df.to_csv(output_path, index=False)
    print(f"Output saved to: {output_path}")

# Example usage:
process("nifty50_5min.csv", "nifty50_strategy_output.csv")
