
import pandas as pd
import numpy as np

file_name = "sbi_1min.csv"
data = pd.read_csv(file_name, parse_dates=['Timestamp2'])
data = data.sort_values('Timestamp2')
#print(data)

'''
Step 1: Calculating Up Moves and Down Moves
First, calculate the bar-to-bar changes for each bar: Chng = Close(t) – Close(t-1)
Up move (U) equals: Close(t) – Close(t-1) if the price change is positive. Zero if the price change is negative or zero
Down move (D) equals: The absolute value of Close(t) – Close(t-1) if the price change is negative. Zero if the price change is positive or zero

Step 2: Averaging the Advances and Declines
AvgU = sum of all up moves (U) in the last N bars divided by N
AvgD = sum of all down moves (D) in the last N bars divided by N

Step 3: Calculating Relative Strength
RS = AvgU / AvgD

Step 4: Calculating the Relative Strength Index (RSI)
RSI = 100 – 100 / ( 1 + RS)
'''

#RSI
RSI = np.empty(len(data))
window_size = 7
U = []
D = []

for i in range (len(data)):

    if i>=1:
        change = data.loc[i,"Close"] - data.loc[i-1,"Close"]
        if change > 0:
            U.append(abs(change))
            D.append(0)
        else:
            U.append(0)
            D.append(abs(change))

        avg_U=0
        avg_D=0
        if i>6:
            for j in range (0,window_size):
                avg_U = avg_U +  U[i-j]
                avg_D = avg_D +  D[i-j]

            avg_U = avg_U / window_size
            avg_D = avg_D / window_size
            if avg_D == 0:
                RS = 0
            else:
                RS = avg_U/avg_D
            rsi = 100 - (100/(1 + RS))
            RSI[i] = rsi
        else:
            avg_U=0
            avg_D=0
            RSI[i] = None

    else:
        U.append(0)
        D.append(0)
        RSI[i] = None

data['RSI'] = RSI
print(data)

