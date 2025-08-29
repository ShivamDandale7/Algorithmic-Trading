import pandas as pd

file_name = "nifty50_1d.csv"
data = pd.read_csv(file_name, parse_dates=['Timestamp2'])
data = data.sort_values('Timestamp2')
#print(data)


#Supertrend
period = 14  # ATR period
multiplier = 3  # Multiplier for ATR

data['ATR'] = 0.0
data['Upperband'] = 0.0
data['Lowerband'] = 0.0
data['Supertrend'] = 0.0
data['Trend'] = 0

for i in range(len(data)):
    if i >= period:
        tr_values = []
        for j in range(period):
            high = data.iloc[i - j]['High']
            low = data.iloc[i - j]['Low']
            close_prev = data.iloc[i - j - 1]['Close']
            tr = max(high - low, abs(high - close_prev), abs(low - close_prev))
            tr_values.append(tr)
        atr = sum(tr_values) / period

        data.at[i, 'ATR'] = atr

        if i == period:
            data.at[i, 'Upperband'] = (data.at[i, 'High'] + data.at[i, 'Low']) / 2 + multiplier * atr
            data.at[i, 'Lowerband'] = (data.at[i, 'High'] + data.at[i, 'Low']) / 2 - multiplier * atr
            if (data.at[i, 'Close'] < data.at[i, 'Upperband']):
                data.at[i, 'Supertrend'] = data.at[i, 'Upperband']
            else:
                data.at[i, 'Supertrend'] = data.at[i, 'Lowerband']
        else:
            prev_close = data.at[i - 1, 'Close']
            prev_upper = data.at[i - 1, 'Upperband']
            prev_lower = data.at[i - 1, 'Lowerband']
            basicUpper = (data.at[i, 'High'] + data.at[i, 'Low']) / 2 + multiplier * atr
            basicLower = (data.at[i, 'High'] + data.at[i, 'Low']) / 2 - multiplier * atr

            if basicUpper < prev_upper or prev_close > prev_upper:
                data.at[i, 'Upperband'] = basicUpper
            else:
                data.at[i, 'Upperband'] = prev_upper

            if basicLower > prev_lower or prev_close < prev_lower:
                data.at[i, 'Lowerband'] = basicLower
            else:
                data.at[i, 'Lowerband'] = prev_lower

            if (data.at[i-1,"Supertrend"] == data.at[i-1, 'Upperband']) and (data.at[i, 'Close'] < data.at[i, 'Upperband']):
                data.at[i, 'Supertrend'] = data.at[i, 'Upperband']
            elif (data.at[i-1,"Supertrend"] == data.at[i-1, 'Upperband']) and (data.at[i, 'Close'] >= data.at[i, 'Upperband']):
                data.at[i, 'Supertrend'] = data.at[i, 'Lowerband']
            elif (data.at[i-1,"Supertrend"] == data.at[i-1, 'Lowerband']) and (data.at[i, 'Close'] >= data.at[i, 'Lowerband']):
                data.at[i, 'Supertrend'] = data.at[i, 'Lowerband']
            elif (data.at[i-1,"Supertrend"] == data.at[i-1, 'Lowerband']) and (data.at[i, 'Close'] < data.at[i, 'Lowerband']):
                data.at[i, 'Supertrend'] = data.at[i, 'Upperband']
            else:
                data.at[i, 'Supertrend'] = 0

            if data.at[i, 'Close'] > data.at[i, 'Supertrend']:
                data.at[i, 'Trend'] = 1
            else:
                data.at[i, 'Trend'] = -1

print(data[[ 'ATR', 'Upperband', 'Lowerband', 'Supertrend','Trend']])

