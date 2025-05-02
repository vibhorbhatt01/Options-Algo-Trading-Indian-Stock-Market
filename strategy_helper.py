

import pyotp
import json
from NorenRestApiPy.NorenApi import NorenApi
import pandas as pd
from datetime import datetime, timedelta,time
import logging
import csv 
from paper_trade import * 


time_formtae = '%d-%m-%Y %H:%M:%S'
api = None
def login():
    #global api
    apicredfile = open("./apicred.json")
    apicredjson = json.load(apicredfile)

    # Credentials
    user = apicredjson["user"]
    pwd = apicredjson["pwd"]
    vc = apicredjson["vc"]
    app_key = apicredjson["app_key"]
    imei = apicredjson["imei"]
    tokentotp = apicredjson["tokentotp"]

    # Enable debug to see requests and responses
    # logging.basicConfig(level=logging.DEBUG)

    class ShoonyaApiPy(NorenApi):
        def __init__(self):
            NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/')
            api = self

    # Start of the program
    api = ShoonyaApiPy()
    ret = api.login(userid=user, password=pwd, twoFA=pyotp.TOTP(tokentotp).now(), vendor_code=vc, api_secret=app_key, imei=imei)

    # Start of the program
    if ret is not None:
        if ret["stat"] == "Ok":
            print("Login successful. User:", ret["uname"])
            return api
        else:
            print("Login unsuccessful.")
            if "emsg" in ret:
                print("Error:", ret["emsg"])
            else:
                print("Unknown error occurred.")
    else:
        print("Login unsuccessful. API response is None. Debug and check for errors.")



def round_down_to_time_frame(minutes):
    from datetime import datetime, timedelta
    current_time = datetime.now()
    rounded_minutes = current_time.minute - (current_time.minute % minutes)
    rounded_time = current_time.replace(minute=rounded_minutes, second=0, microsecond=0)
    adjusted_time = rounded_time - timedelta(minutes=minutes)
    return adjusted_time.strftime('%Y-%m-%d %H:%M:%S') 



def extract_expiry_date(dname):
    parts = dname.split()
    date_str = parts[1]
    return pd.to_datetime(date_str, format='%d%b%y')


def exchange_valuestrike_selection(api, serchsym, token_value, exchange_value, strike_gap, strike, month, optt):
    print("Running exchange_valuestrike_selection")
    symbol = serchsym

    qt = api.get_quotes(exchange_value, token_value)
    print(qt)
    if qt is not None:
        lp_value = float(qt["lp"])
        rounded = round(lp_value / strike_gap) * strike_gap
        ce_strike_price = strike * strike_gap + rounded
        pe_strike_price = round(lp_value / strike_gap) * strike_gap - strike * strike_gap

        print(symbol, pe_strike_price, ce_strike_price)
    else:
        raise ValueError("Not able to get LTP value from broker")

    print("Getting strike fun is running...")
    if optt == "PE":
        symbol_check = pe_strike_price
    elif optt == "CE":
        symbol_check = ce_strike_price
    else:
        print("Invalid option type")
        return None

    option_type = optt
    query = f"{symbol} {symbol_check} {option_type}"

    ret = api.searchscrip(exchange="NFO", searchtext=query)
    print(ret)

    try:
        values = ret.get("values", [])
    except AttributeError:
        print("No data available.")
        return None

    if not values:
        print("No values found.")
        return None

    df = pd.DataFrame(values)
    df['expiry_date'] = df['dname'].apply(extract_expiry_date)
    #print(df)
    df['expiry_date'] = pd.to_datetime(df['expiry_date'])

    today_date = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))
    filtered_df = df[df['expiry_date'] > today_date]

    if filtered_df.empty:
        print("No valid options found with expiry date equal to or greater than today's date.")
        return None

    tysm_value = filtered_df.iloc[0]['tsym']
    token_value = filtered_df.iloc[0]['token']
    exchange_value = filtered_df.iloc[0]['exch']
    # print(tysm_value,token_value,exchange_value)
    return tysm_value, token_value, exchange_value

# petysm_value, petoken_value, peexchange_value,cetysm_value, cetoken_value, ceexchange_value = exchange_valuestrike_selection(api,"BANKNIFTY", token_value,exchange_value)
def get_symbol(api,symbol):

    query = f"{symbol}"
    
    # Assuming the `api` object is defined and accessible here
    ret = api.searchscrip(exchange="NSE", searchtext=query)
    #print(ret)
    data_values = ret['values'][0]  # Assuming there's only one item in 'values'
    token = data_values['token']
    tsym = data_values['tsym']
    exch = data_values['exch']
    return token,tsym ,exch


# token,tsym ,exch = get_symbol(api,"NIFTY BANK")
# print(token,tsym ,exch)

# tysm_value, token_value, exchange_value = exchange_valuestrike_selection(api=api,serchsym=tsym, token_value=token,exchange_value=exch,strike_gap=100,strike=0,month="JUL",optt="PE")

# print(tysm_value, token_value, exchange_value)



def exit_all_positions(api):
    
    ret = api.get_positions()

    if ret:
        for i in ret:
            mtm = float(i['urmtom'])
            pnl = float(i['rpnl'])
            day_m2m = mtm + pnl
            i['Daily MTM'] = day_m2m

            symbol = i['tsym']
            quantity = int(i['netqty'])
            product_type = i['prd']
            exchange = i['exch']

            if quantity < 0:
                api.place_order(buy_or_sell='BUY', product_type=product_type,
                                exchange=exchange, tradingsymbol=symbol,
                                quantity=abs(quantity), discloseqty=0, price_type='MKT',
                                retention='DAY', remarks='RASH ALGO ')

                print(f"Market order executed to buy symbol {symbol} with quantity {abs(quantity)}.")
            elif quantity > 0:
                api.place_order(buy_or_sell='SELL', product_type=product_type,
                                exchange=exchange, tradingsymbol=symbol,
                                quantity=quantity, discloseqty=0, price_type='MKT',
                                retention='DAY', remarks='RASH ALGO ')

                print(f"Market order executed to sell symbol {symbol} with quantity {quantity}.")
            else:
                print(f"Position for symbol {symbol} has already been exited.")
    else:
        print("No positions found.")



def cancel_orders_all(api):
    ret = api.get_order_book()
    
    # Check if data is empty
    if not ret:
        print("No data available.column not found. its due to 1st order if came in 2nd order then its problem")
        return
    
    df = pd.DataFrame(ret)
    
    # Check if 'status' column exists in the DataFrame
    if 'status' not in df.columns:
        print("Invalid data format. 'status'")
        return
    
    df_filtered = df[(df["status"] == "OPEN") | (df["status"] == "TRIGGER_PENDING")]
    
    order_numbers = df_filtered['norenordno']

    canceled_orders = []  # List to store canceled order numbers

    if order_numbers.empty:
        print("No open positions.")
    else:
        for index, orderno in enumerate(order_numbers, start=1):
            api.cancel_order(orderno=orderno)
            canceled_orders.append(orderno)

    # Prepare canceled orders message
    canceled_message = ""
    if canceled_orders:
        for index, orderno in enumerate(canceled_orders, start=1):
            canceled_message += f"Canceled order {index}: {orderno}\n"
    else:
        canceled_message = "No orders were canceled."

    print(canceled_message)        






api = login()



def inside_give_open_df():
    file_path = "PAPER_TRADE.csv"
    df = pd.read_csv(file_path)
    df_test = df.groupby(['order_id','Symbol','token_value','main_symbol', 'Option_Type','exchange_value'])['Qty'].sum().reset_index()
    buy_df = df[df['BUY_sell_exit'].isin(['BUY', 'SELL'])]
    result_df = pd.merge(df_test, buy_df[['order_id', 'token_value','Date','option_lp',"BUY_sell_exit"]], on='order_id', how='left')
    OPEN_DF = result_df[result_df['Qty'] != 0]
    #print(OPEN_DF)
    return OPEN_DF
    


def INSIDE_APPEND_DATA_TO_CSV(df):
    df_selected = df[['order_id', 'Symbol', 'token_value_x', 'Date', 'option_lp', 'current_lp', 'pnl']].copy()
    
    df_selected.columns = ['orderid', 'symbol', 'token_value', 'trade_date', 'option_lp', 'current_lp', 'pnl']
    
    df_selected['current_time'] = pd.Timestamp.now()
    
    csv_file = 'pnl.csv'
    
    df_selected.to_csv(csv_file, mode='a', header=not pd.io.common.file_exists(csv_file), index=False)    


def inside_get_highest_lowest_pnl(orderid, symbol, trade_date):
    csv_file = 'combine_pnl.csv'
    
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file)
    df['Date'] = pd.to_datetime(df['Date'])
    trade_date = pd.to_datetime(trade_date)
    filtered_df = df[(df['Date'] == trade_date)]
    #filtered_df.to_csv("testpnl.csv")
    #print(filtered_df)
    if not filtered_df.empty:
        max_pnl = filtered_df['total_current_pnl'].max()
        min_pnl = filtered_df['total_current_pnl'].min()
        return max_pnl, min_pnl
    else:
        return None, None

def inside_csv_append_combine_pnl(df):
            #print(df)
            df['total_current_pnl'] = df.groupby('Date_only')['pnl'].transform('sum')
            df['current_time'] = pd.Timestamp.now()

            
            df.to_csv("combine_pnl.csv", mode='a', header=not pd.io.common.file_exists("combine_pnl.csv"), index=False)     

def calculate_total_pnl(date_str, df):
    # Convert 'Date' column to datetime
    df['traded_date'] = pd.to_datetime(df['traded_date'])
    # Convert the input date string to a datetime object
    target_date = pd.to_datetime(date_str)

    filtered_df = df[df['traded_date'].dt.date == target_date.date()]

    total_pnl = filtered_df['TRADE_PNL'].sum()
    return total_pnl



def append_open_ltp_pnl_to_csv():
    file_path = "PAPER_TRADE.csv"
    df = pd.read_csv(file_path)
    
    #print(df)
    exit_df = df[df['BUY_sell_exit'] == 'EXIT']
    # print(exit_df)
    
    df = inside_give_open_df()
    if not df.empty:               
        df['pnl'] = 0.0
        df['current_lp'] = 0.0
        
        # Iterate over each order_id and symbol
        for index, row in df.iterrows():
            qty = row['Qty']
            token_value = row['token_value_x']
            exchange_value = row['exchange_value']
            token_value = str(token_value)
            exchange_value = str(exchange_value)
            lp_value = ltp(api, exchange_value, token_value)  # Get lp_value from the ltp function
            entry_lp = row['option_lp']
            BUY_sell_exit = row['BUY_sell_exit']
            if lp_value is None:
                lp_value = entry_lp
        
            if lp_value is not None:
                df.at[index, 'current_lp'] = lp_value  # Set the current_lp value
                if BUY_sell_exit == "BUY":
                    if lp_value > entry_lp:
                        PT = lp_value - entry_lp
                        pro = PT * qty
                        TRADE_PNL = pro
                    elif lp_value < entry_lp:
                        PT = entry_lp - lp_value
                        pro = PT * qty
                        TRADE_PNL = -pro
                    else:
                        PT = lp_value - entry_lp
                        pro = PT * qty
                        TRADE_PNL = pro
                elif BUY_sell_exit == "SELL":
                    if lp_value < entry_lp:
                        PT = lp_value - entry_lp
                        pro = PT * qty
                        TRADE_PNL = pro
                    elif lp_value > entry_lp:
                        PT = entry_lp - lp_value
                        pro = PT * qty
                        TRADE_PNL = -pro
                    else:
                        PT = lp_value - entry_lp
                        pro = PT * qty
                        TRADE_PNL = pro
                
                df.at[index, 'pnl'] = TRADE_PNL
        
        # print(df)
        if not df.empty:
            ## data append to csv is must
            INSIDE_APPEND_DATA_TO_CSV(df)

            df['Date'] = pd.to_datetime(df['Date'])
            
            # Extract the date part (ignoring time) for grouping
            df['Date_only'] = df['Date'].dt.date
            

            inside_csv_append_combine_pnl(df)
 
            df[['max_pnl', 'min_pnl']] = df.apply(lambda row: pd.Series(inside_get_highest_lowest_pnl(row['order_id'], row['Symbol'], row['Date'])), axis=1)


            df['exit_total_pnl'] = df['Date_only'].apply(lambda date: calculate_total_pnl(date, exit_df))
            df['total_pnl_exit_plus_close'] = df['max_pnl'] + df['exit_total_pnl']
            
            print(df)
            
            df.to_csv('test_NO_USE_APPEND.csv')

            return df  # Return the DataFrame if it's not empty
    else:
        return None  # Return None if the DataFrame is empty

# append_open_ltp_pnl_to_csv()


def check_trade_data( main_symbol, option_type):

    today = datetime.today().date()
    
    # Read the CSV file
    with open("trade_data.csv", mode='r') as file:
        reader = csv.DictReader(file)
        
        # Loop through each row in the CSV
        for row in reader:
            # Convert the date in the row to a datetime object
            row_date = datetime.strptime(row['Date'], '%Y-%m-%d %H:%M:%S.%f').date()
            
            # Check if the date, main_symbol, and option_type match
            if row_date == today and row['main_symbol'] == main_symbol and row['Option_Type'] == option_type:
                return 1
    return 0
