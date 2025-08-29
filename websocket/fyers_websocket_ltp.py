from fyers_apiv3.FyersWebsocket import data_ws

client_id = open("client_ID.txt",'r').read()
access_token = open("access_token.txt",'r').read()

def onmessage(message):
    """
    Callback function to handle incoming messages from the FyersDataSocket Websocket
    Parameters:
            message (dict): The received message from the WebSocket 
    """
    print("Response:", message)
    print("Symbol:",message['symbol'],  "ltp: ",message['ltp'])
    print("Symbol:",message['symbol'],  "Volume: ",message['vol_traded_today'])


def onerror(message):
    """
    Callback function to handle Websocket errors
    Parameters:
            message (dict): The error message received from the WebSocket 
    """

    print("Error", message)


def onclose(message):
    """
    Callback function to handle Websocket connection close events. 
    """

    print("Connection Closed", message)


def onopen():
    """
    Callback function to subscribe to data type and symbols upon Websocket connection. 
    """
    # Specify the data type and symbols you want to subscribe to
    data_type = "SymbolUpdate"

    # Subscribe to the specified symbols and data types
    symbols = ['MCX:CRUDEOIL25SEPFUT']
    fyers.subscribe(symbols=symbols, data_type=data_type)

    # Keep the socket running to receive real-time data
    fyers.keep_running()


# Create a FyersDataSocket instance with the provided parameters
fyers = data_ws.FyersDataSocket(
    access_token=access_token,      # Access token in format "appid:accesstoken"
    log_path="",                    # Path to save logs. Leave empty to auto-create logs in the current directory
    litemode=False,                 # Lite mode disabled. Set to True if you want a lite response.
    write_to_file=False,            # Save response in a log file instead of printing it.
    reconnect=True,                 # Enable auto-reconnection to WebSocket on disconnection.
    on_connect=onopen,              # Callback function to subscribe to data upon connection.
    on_close=onclose,               # Callback function to handle WebSocket connection close events.
    on_error=onerror,               # Callback function to handle WebSocket errors.
    on_message=onmessage            # Callback function to handle incoming messages from the WebSocket.
)

fyers.connect()