
import pandas as pd

file_name = "sbi_1min.csv"
data =  pd.read_csv(file_name)
data = data.sort_values('Timestamp2')

# Calculating SMA
sma_list = []
period = 14
sma_val = 0

for index, row in data.iterrows():
    if index >= period -1:
        sma_val = 0
        for i in range(0,period):
            sma_val = sma_val + data.iloc[index-i]['Close']
        sma_val = sma_val / period
        sma_list.append(sma_val)
    
    else:
        sma_list.append(None)

data['SMA'] = sma_list
print(data)