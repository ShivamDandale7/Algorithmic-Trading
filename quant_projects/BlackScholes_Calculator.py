import math
import yfinance as yf
import numpy as np
import pandas as pd
from scipy.stats import norm
from fyers_apiv3 import fyersModel
import pytz

#generate trading session
client_id = open("client_ID.txt",'r').read()
access_token = open("access_token.txt",'r').read()
interval = "1D"

# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="D:\FyiersApiAutomation\logs")

def fetchOHLC(ticker,interval,range_from, range_to):
    data = {
        "symbol":ticker,
        "resolution":interval,
        "date_format":"1",
        "range_from":range_from,
        "range_to":range_to,
        "cont_flag":"1"
    }

    response = fyers.history(data=data)['candles']

    # Create a DataFrame
    columns = ['Timestamp','Open','High','Low','Close','Volume']
    df = pd.DataFrame(response, columns=columns)

    # Convert Timestamp to datetime in UTC
    df['Date'] = pd.to_datetime(df['Timestamp'],unit='s').dt.tz_localize(pytz.utc)

    # Convert Timestamp to IST
    ist = pytz.timezone('Asia/Kolkata')
    df['Date'] = df['Date'].dt.tz_convert(ist)

    return (df['Date','Close'])

# data = fetchOHLC("NSE:NIFTY50-INDEX", "1D", "2025-08-17", "2025-10-16")
# print(data)


def black_scholes_model(S, K, T, r, sigma, option_type):
    d1 = ((math.log(S/K)) + (r + 0.5*(sigma**2))*T) / (sigma* math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if option_type == 'call':
      option_price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    elif option_type == 'put':
      option_price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    else:
      raise ValueError("Option Type must be 'call' or 'put'")

    return option_price, d1, d2

def calculate_option_greeks(S, K, T, r, sigma, option_type):

    option_price, d1, d2 = black_scholes_model(spot_price, K, T, r, sigma, option_type)
    if option_type == 'call':
        # Delta
        delta = norm.cdf(d1)

        # Gamma (same for call and put)
        gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))

        # Vega (same for call and put)
        vega = S * norm.pdf(d1) * math.sqrt(T)

        # Theta
        theta = (-S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm.cdf(d2))

        # Rho
        rho = K * T * math.exp(-r * T) * norm.cdf(d2)

    elif option_type == 'put':
        # Delta
        delta = norm.cdf(d1) - 1

        # Gamma (same for call and put)
        gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))

        # Vega (same for call and put)
        vega = S * norm.pdf(d1) * math.sqrt(T)

        # Theta
        theta = (-S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * norm.cdf(-d2))

        # Rho
        rho = -K * T * math.exp(-r * T) * norm.cdf(-d2)

    else:
        raise ValueError("option_type must be 'call' or 'put'")

    return delta, gamma

def calculate_annualized_volatility(ticker, interval, start_date, end_date):
  stock_df = fetchOHLC(ticker, interval, range_from=start_date, range_to=end_date)
  stock_df['Log Returns'] = np.log(stock_df['Close']/stock_df['Close'].shift(1))
  rolling_volatility = stock_df['Log Returns'].rolling(90).std()
  annualized_volatility = rolling_volatility * math.sqrt(252)
  return annualized_volatility

data = calculate_annualized_volatility("NSE:NIFTY50-INDEX","1D","2025-08-17","2025-10-16")
print(data)
# Reading excel file for input
file_path = 'D:/FyiersApiAutomation/quant_projects/input_option_data.xlsx'
df = pd.read_excel(file_path)

df['Stock'] = "NSE:" + df['Stock'].astype(str) + "-INDEX"

df['Spot Price'] = np.nan
df['Annualized Volatility'] = np.nan
df['Trading days to expiry'] = np.nan
df['Theo Option Price'] = np.nan

for index, row in df.iterrows():
    stock = row['Stock']
    date = pd.to_datetime(row['Date'])
    expiry_dt = pd.to_datetime(row['Expiry Date'])

    start = (date - pd.DateOffset(90)).strftime('%Y-%m-%d')
    end = date.strftime('%Y-%m-%d')
    print(start)
    print(end)

    try:
        print("hello")
        print(start)
        print(end)

        annualized_vola = calculate_annualized_volatility(stock, interval, start, end)
        df.at[index, 'Annualized Volatility'] = annualized_vola[-1]
        print(annualized_vola)
        
        trading_days = np.busday_count(date.date(), expiry_dt.date())
        df.at[index, 'Trading Days to Expiry'] = trading_days

        spot_data = fetchOHLC(
                          stock,
                          interval,
                          range_from=date.strftime('%Y-%m-%d'),
                          range_to=(date + pd.DateOffset(days=1)).strftime('%Y-%m-%d')
                          )

        spot_price = spot_data['Close'].iloc[0]
        df.at[index, 'Spot Price'] = spot_price

        K = row['Strike']
        T = trading_days/252
        r = 0.065
        sigma = annualized_vola[-1]

        if row['CE/PE'] == 'CE':
          option_type = 'call'
        else:
          option_type = 'put'

        option_price = black_scholes_model(spot_price, K, T, r, sigma, option_type)
        df.at[index, 'Theo Option Price'] = option_price[0]


        # Calculating Greeks
        delta, gamma = calculate_option_greeks(spot_price, K, T, r, sigma, option_type)
        df.at[index, 'Delta'] = delta
        df.at[index, 'Gamma'] = gamma

    except Exception as e:
        print(f"could not calculate values for {stock} on {date}: {e}")

# Creating output file
with pd.ExcelWriter("D:/FyiersApiAutomation/quant_projects/option_model_values.xlsx", engine='openpyxl') as writer:
  df.to_excel(writer, index=False)