from fyers_apiv3 import fyersModel
import webbrowser

# input parameters
redirect_uri = "https://www.google.com"
client_id = "EZ97MQK2YZ-100"
secret_key = "A323Q159ZV"

grant_type = "authorization_code"                 
response_type = "code"                           
state = "sample"  

### Connect to the sessionModel object here with the required input parameters
appSession = fyersModel.SessionModel(client_id = client_id, redirect_uri = redirect_uri,response_type=response_type,state=state,secret_key=secret_key,grant_type=grant_type)

### Make  a request to generate_authcode object this will return a login url which you need to open in your browser from where you can get the generated auth_code 
generateTokenUrl = appSession.generate_authcode()

print((generateTokenUrl))  
webbrowser.open(generateTokenUrl,new=1)

### After succesfull login the user can copy the generated auth_code over here and make the request to generate the accessToken 
auth_code = input("Enter Auth Code Generated: ")
appSession.set_token(auth_code)
response = appSession.generate_token()

try: 
    access_token = response["access_token"]
except Exception as e:
    print(e,response)  ## This will help you in debugging then and there itself like what was the error and also you would be able to see the value you got in response variable. instead of getting key_error for unsuccessfull response.

## Once you have generated accessToken now we can call multiple trading related or data related apis after that in order to do so we need to first initialize the fyerModel object with all the requried params.

fyers = fyersModel.FyersModel(token=access_token,is_async=False,client_id=client_id,log_path="D:\FyiersApiAutomation\logs")

response = fyers.get_profile()
print(response)

# save to txt file
with open("client_ID.txt",'w') as file:
    file.write(client_id)

with open("secret_key.txt",'w') as file:
    file.write(secret_key)

with open("access_token.txt",'w') as file:
    file.write(access_token)