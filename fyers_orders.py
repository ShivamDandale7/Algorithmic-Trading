
import datetime
from fyers_apiv3 import fyersModel

#generate trading session
client_id = open("client_ID.txt",'r').read()
access_token = open("access_token.txt",'r').read()

# Initialize the FyersModel instance with your client_id, access_token, and enable async mode
fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="D:\FyiersApiAutomation\logs")

def placeOrder(inst ,t_type,qty,order_type,price=0, price_stop=0):
    exch = inst[:3]
    symb = inst[4:]
    dt = datetime.datetime.now()
    print(dt.hour,":",dt.minute,":",dt.second ," => ",t_type," ",symb," ",qty," ",order_type," @ price =  ",price)
    if(order_type=="MARKET"):
        type1 = 2
        price = 0
        price_stop = 0
    elif(order_type=="LIMIT"):
        type1 = 1
        price_stop = 0
    elif(order_type=="SL-LIMIT"):
        type1 = 4

    if(t_type=="BUY"):
        side1=1
    elif(t_type=="SELL"):
        side1=-1

    data =  {
        "symbol":inst,
        "qty":qty,
        "type":type1,
        "side":side1,
        "productType":"CNC",
        "limitPrice":price,
        "stopPrice":price_stop,
        "validity":"DAY",
    }

    try:
        orderid = fyers.place_order(data)
        print(dt.hour,":",dt.minute,":",dt.second ," => ", symb , orderid)
        return orderid
    except Exception as e:
        print(dt.hour,":",dt.minute,":",dt.second ," => ", symb , "Failed : {} ".format(e))


def cancelOrder(order_id):
    #convert id into dictionary
    order_id_dict = {"id": str(order_id)}
    response = fyers.cancel_order(order_id_dict)
    print(response)


def modifyOrder(orderId,order_type,qty,price=0, price_stop=0):
    if(order_type=="MARKET"):
        type1 = 2
        price = 0
        price_stop = 0
    elif(order_type=="LIMIT"):
        type1 = 1
        price_stop = 0
    elif(order_type=="SL-LIMIT"):
        type1 = 4

    data = {
        "id":str(orderId),
        "type":type1,
        "limitPrice": price,
        "qty":qty
    }
    print(data)
    response = fyers.modify_order(data=data)
    print(response)



#placeOrder("NSE:SBIN-EQ" ,'SELL',1,"MARKET")
#placeOrder("NSE:SBIN-EQ" ,'BUY',1,"LIMIT",804)
#placeOrder("NSE:SBIN-EQ" ,'SELL',1,"SL-LIMIT",579,580)

cancelOrder(25053100004850)
#modifyOrder(230913003523,"MARKET",1)