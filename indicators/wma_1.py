
import pandas as pd 

# Weighted moving average
file_path = "sbi_1min.csv"
data = pd.read_csv(file_path,parse_dates=['Timestamp2'])
data = data.sort_values('Timestamp2')

wma_list = []
period = 4
wma_value = 0
wma_percent = [0.40,0.30,0.20,0.10]

for i in range(len(data)):
    if i >= period - 1:
        wma_value = 0
        for j in range(0,period):
            wma_value = wma_value + (data.iloc[i-j]['Close'])*wma_percent[j]
        wma_list.append(wma_value)
    
    else:
        wma_list.append(None)

data['WMA'] = wma_list
print(data)