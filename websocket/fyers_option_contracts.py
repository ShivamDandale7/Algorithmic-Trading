
from fyers_apiv3 import fyersModel
import pandas as pd
import datetime as dt
import numpy as np

#generate trading session
client_id = open("client_id.txt",'r').read()
access_token = open("access_token.txt",'r').read()

# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")

def instrumentList():
    url = "https://public.fyers.in/sym_details/NSE_FO.csv"
    df = pd.read_csv(url)
    df.dropna(axis=1, how='all', inplace=True)
    #df.to_csv("temp0.csv")
    # Read the CSV file from the URL into a DataFrame
    column_names = ["token","description", "temp1", "temp2", "temp3", "temp4", "updatedOn", "updatedAt", "ticker",
                    "temp6", "temp7", "token2", "symbol", "token_spot", "strike", "cepe", "temp8", "temp9", "temp10"]
    # Set column names
    df.columns = column_names
    #df.to_csv("temp2.csv")
    #df = pd.read_csv(url, names=column_names, header=None)
    df = df.drop(columns=['temp1', 'temp2', 'temp3','temp4','temp6','temp7','temp8','temp9'], errors='ignore')
    #df.to_csv("temp1.csv")
    df['extractedDate'] = df['description'].str.extract(r'(\d{2} \w{3} \d{2})')
    # Convert the "ExtractedDate" column to datetime format
    df['expiry'] = pd.to_datetime(df['extractedDate'], format='%y %b %d')

    return df

df_instrument_list = instrumentList()
df_instrument_list.to_csv("instrumentList.csv")

def option_contracts(symbol, option_type="CE"):
    option_contracts = []
    for index, row in df_instrument_list.iterrows():
        if row["symbol"]==symbol and row["cepe"]==option_type:
            option_contracts.append(row)
    return pd.DataFrame(option_contracts)
        
df_opt_contracts = option_contracts("BANKNIFTY")
print(df_opt_contracts)

#function to extract the closest expiring option contracts
def option_contracts_closest(ticker, duration = 0, option_type="CE"):
    #duration = 0 means the closest expiry, 1 means the next closest
    df_opt_contracts = option_contracts(ticker)
    df_opt_contracts["time_to_expiry"] = (pd.to_datetime(df_opt_contracts["expiry"]) - dt.datetime.now()).dt.days
    min_day_count = np.sort(df_opt_contracts["time_to_expiry"].unique())[duration]
    
    return (df_opt_contracts[df_opt_contracts["time_to_expiry"] == min_day_count]).reset_index(drop=True)

df_opt_contracts_closest = option_contracts_closest("BANKNIFTY",0)
print(df_opt_contracts_closest)

#find spot price
data = {
    "symbols":"NSE:NIFTYBANK-INDEX"
}
response = fyers.quotes(data=data)
underlying_price = response['d'][0]['v']['lp']
print("LTP: ", underlying_price)

#function to find the ATM data
def option_contracts_atm(ticker, underlying_price, duration = 0, option_type="CE"):
    #duration = 0 means the closest expiry, 1 means the next closest
    df_opt_contracts_closest = option_contracts_closest(ticker,duration)

    df_sorted = df_opt_contracts_closest.sort_values(by='strike')
    differences = df_sorted['strike'].diff()
    min_difference = int(differences.min())
    print("The difference between 2 strikes is ", min_difference)

    closest_atm = round(underlying_price/min_difference,0)*min_difference
    final_contracts = []
    for index, row in df_opt_contracts_closest.iterrows():
        if row["symbol"]==ticker and row["strike"]==closest_atm:
            final_contracts.append(row)
    return pd.DataFrame(final_contracts)

atm_contract = option_contracts_atm("BANKNIFTY",underlying_price)
print(atm_contract)

for column, value in atm_contract.iloc[0].items():
    print(f"{column}: {value}")

