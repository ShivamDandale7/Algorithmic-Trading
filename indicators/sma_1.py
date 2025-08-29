import pandas as pd

file_path = "sbi_1min.csv"
data = pd.read_csv(file_path)
data = data.sort_values('Timestamp2')

# Calculating SMA
data['SMA'] = data['Close'].rolling(window=14).mean()

print(data)