
import pandas as pd

# Exponential Moving average
file_path = "sbi_1min.csv"
data = pd.read_csv(file_path,parse_dates=['Timestamp2'])
data = data.sort_values('Timestamp2')

ema = data['Close'].ewm(span=14).mean()
data['EMA'] = ema
print(data)