
import pandas as pd

file_name = "nifty50_1d.csv"
data = pd.read_csv(file_name, parse_dates=['Timestamp2'])
data = data.sort_values('Timestamp2')
#print(data)

#Stochastics
lookback_period = 14  # Lookback period for Stochastic Oscillator

K = []
D = []

for i in range (len(data)):

    if i>=lookback_period:

        highest_high = 0
        lowest_low = 1000000
        for j in range (lookback_period):
            highest_high = max(highest_high, data.loc[i-j, "High"])
            lowest_low = min(lowest_low, data.loc[i-j, "Low"])

        k_value = (data.loc[i,"Close"] - lowest_low)*100 / (highest_high - lowest_low)
        K.append(k_value)

        if i >= lookback_period + 3:
            d_value = (K[i] + K[i-1] + K[i-2]) / 3
            D.append(d_value)
        else:
            D.append(0)

    else:
        K.append(0)
        D.append(0)

data['K'] = K
data['D'] = D
print(data)