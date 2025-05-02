import os 
import pandas as pd 
import random

def exitdf():
    file_path = "PAPER_TRADE.csv"    
    csv_file_path = file_path
    df = pd.read_csv(csv_file_path)

    #total_option_data_df = df.groupby(['order_id','Symbol','token','main_symbol', 'Option_Type','exchange_value',])['Qty'].sum().reset_index()
    symbol_sum_qty_df = df.groupby(['order_id','Symbol','main_symbol', 'Option_Type','exchange_value',])['Qty'].sum().reset_index()
    #print(symbol_sum_qty_df)

    if not symbol_sum_qty_df.empty:
        filtered_df = symbol_sum_qty_df[symbol_sum_qty_df['Qty'] != 0]
        print(filtered_df)

# exitdf()

def ltp(api,exchange_value,token_value):
    qt = api.get_quotes(exchange_value, token_value)
    #print(qt)
    if qt is not None:
        lp_value = float(qt["lp"])
        return lp_value
    else:
        return None


def data_per_csv(selected_symbol):
    file_path = "PAPER_TRADE.csv"
    total_open_qty = 0
    symbol_open_qty = 0
    total_qty_sum_pe= 0
    total_qty_sum_ce = 0
    total_fut_qty = 0
    csv_file_path = file_path
    df = pd.read_csv(csv_file_path)
    if selected_symbol is None:
        symbol_filtered_df = df
    else:
        symbol_filtered_df = df[df['main_symbol'] == selected_symbol]
    #print(symbol_filtered_df)
    df_test = df.groupby(['order_id','Symbol','token_value','main_symbol', 'Option_Type','exchange_value'])['Qty'].sum().reset_index()
    #print(df)
    buy_df = df[df['BUY_sell_exit'].isin(['BUY', 'SELL'])]
    result_df = pd.merge(df_test, buy_df[['order_id', 'token_value','Date','option_lp',"BUY_sell_exit"]], on='order_id', how='left')
    OPEN_DF = result_df[result_df['Qty'] != 0]
    symbol_sum_qty_df = symbol_filtered_df.groupby(['order_id','Symbol','token_value','main_symbol', 'Option_Type','exchange_value',])['Qty'].sum().reset_index()
    #print(symbol_sum_qty_df)
    symbol_open_qty = abs(symbol_sum_qty_df['Qty']).sum()



    #total_option_data_df = df.groupby(['order_id','Symbol','main_symbol', 'Option_Type'])['Qty'].sum().reset_index()
    total_option_data_df = symbol_filtered_df.groupby(['order_id','Symbol','main_symbol', 'Option_Type','exchange_value',])['Qty'].sum().reset_index()
    
    ce_filtered_df = total_option_data_df[total_option_data_df['Option_Type'] == 'CE']
    pe_filtered_df = total_option_data_df[total_option_data_df['Option_Type'] == 'PE']

    #total_option_qty = abs(total_option_data_df['Qty']).sum()
    total_qty_sum_ce = abs(ce_filtered_df['Qty']).sum()
    total_qty_sum_pe = abs(pe_filtered_df['Qty']).sum()

    total_open_qty = total_qty_sum_ce+total_qty_sum_pe
    #print(symbol_sum_qty_df)


    return total_qty_sum_ce,total_qty_sum_pe,total_open_qty,symbol_open_qty,symbol_sum_qty_df,total_option_data_df,df_test,OPEN_DF,ce_filtered_df,pe_filtered_df


def get_total_qty(main_symbol):
   total_qty_sum_ce,total_qty_sum_pe,total_open_qty,symbol_open_qty,symbol_sum_qty_df,total_option_data_df,df_test,OPEN_DF,ce_filtered_df,pe_filtered_df =  data_per_csv(selected_symbol=main_symbol)
   return total_open_qty

def generate_unique_number():
    import time
    current_time = int(time.time() * 1000)  # Get current time in milliseconds
    unique_number = current_time * 1000 + random.randint(0, 999)
    return unique_number



def inside_order_live(api,quantity,product_type,exchange,symbol):
    if quantity > 0:
        api.place_order(buy_or_sell='B', product_type="M",
                        exchange=exchange, tradingsymbol=symbol,
                        quantity=abs(quantity), discloseqty=0, price_type='MKT',
                        retention='DAY', remarks='RASH ALGO ')

        print(f"Market order executed to buy symbol {symbol} with quantity {abs(quantity)}.")
    elif quantity < 0:
        api.place_order(buy_or_sell='S', product_type="M",
                        exchange=exchange, tradingsymbol=symbol,
                        quantity=abs(quantity), discloseqty=0, price_type='MKT',
                        retention='DAY', remarks='RASH ALGO ')

        print(f"Market order executed to sell symbol {symbol} with quantity {quantity}.")
    else:
        print(f"Position for symbol {symbol} has already been exited.")


def place_order(api,symbol,token_value, main_symbol,qty, optt,live_trade,reason):
    print('placing order running')
    total_qty_sum_ce,total_qty_sum_pe,total_open_qty,symbol_open_qty,symbol_sum_qty_df,total_option_data_df,df_test,OPEN_DF,ce_filtered_df,pe_filtered_df =  data_per_csv(selected_symbol=main_symbol)


    
    file_exists = os.path.exists('PAPER_TRADE.csv')
    exchange_value = "NFO"    
    lp_value = ltp(api,exchange_value,token_value)
    if lp_value is not None:
            
        if qty < 0: 
            buy_sell = "SELL"     
        elif qty > 0:
            buy_sell = "BUY"
        
        #print(buy_sell)
        order_id = generate_unique_number()    
        update_data = pd.DataFrame({
            'order_id':[order_id],
            'Date': pd.Timestamp.now(),
            "traded_date" : pd.Timestamp.now(),
            'Symbol': [symbol],
            'token_value' : [token_value],
            'main_symbol': [main_symbol],
            'Option_Type': [optt],
            'Qty': [qty],
            'option_lp': [lp_value],
            'BUY_sell_exit': [buy_sell],
            "exchange_value":[exchange_value],
            "TRADE_PNL":[00],
            'profit_or_loss' : [None],                
            "reason":[reason]
        })
    
        update_data_2 = pd.DataFrame({
            'Date': pd.Timestamp.now(),
            'Symbol': [symbol],
            'token_value' : [token_value],
            'main_symbol': [main_symbol],
            'Option_Type': [optt],
            'Qty': [qty],
            'option_lp': [lp_value],
            'BUY_sell_exit': [buy_sell],
            "exchange_value":[exchange_value],       
            "reason":[reason]
        })
    
        # If the file doesn't exist or is empty, create it with a header
        if not file_exists or os.path.getsize('PAPER_TRADE.csv') == 0:
            update_data.to_csv('PAPER_TRADE.csv', mode='w', header=True, index=False)
            update_data_2.to_csv('trade_data.csv', mode='w', header=True, index=False)
        else:
            update_data.to_csv('PAPER_TRADE.csv', mode='a', header=False, index=False)
            update_data_2.to_csv('trade_data.csv', mode='a', header=False, index=False)
        if live_trade :
            qty =qty
            exch = "NFO"
            symbol = symbol
            inside_order_live(api=api,quantity=qty,product_type='MKT',exchange=exch,symbol=symbol)
        return lp_value,symbol
    else:
        print("lp value is none not appending data contact devloper 7014403338 RASH_ALGO")  
        return None,None

   



def exit_position_all(api,live_trade,reason) :
    total_qty_sum_ce,total_qty_sum_pe,total_open_qty,symbol_open_qty,symbol_sum_qty_df,total_option_data_df,df_test,OPEN_DF,ce_filtered_df,pe_filtered_df =  data_per_csv(selected_symbol=None)
    df_csv = OPEN_DF
    print(OPEN_DF)
    if df_csv is not None :
            
        open_position_df = df_csv
        for index, row in open_position_df.iterrows():
            print(row)
            order_id = row['order_id']
            main_symbol = row['main_symbol']
            symbol = row['Symbol']
            qty = row['Qty']  
            Option_Type = row["Option_Type"] 
            exchange_value = row['exchange_value']
            entry_lp = row['option_lp']
            BUY_sell_exit = row['BUY_sell_exit']
            token_value = str(row['token_value_x'])


            if qty != 0 and symbol == symbol :

    
                if qty != 0:
                    # Determine the opposite quantity and symbol
                    opposite_qty = -qty
    
                    lp_value=ltp(api,exchange_value,token_value)

                    if lp_value is not None:
                        if BUY_sell_exit == "BUY":
                            if lp_value > entry_lp :
                                    
                                profit_loss = "PROFIT"
                                PT = lp_value - entry_lp
                                pro = PT * qty
                                TRADE_PNL = pro
                            elif lp_value < entry_lp :
                                profit_loss = "LOSS"   
                                PT = entry_lp - lp_value
                                pro = PT * qty
                                TRADE_PNL = -pro     
                            else:
                                profit_loss = "CTC"
                                PT = lp_value - entry_lp
                                pro = PT * qty
                                TRADE_PNL = pro

                        elif BUY_sell_exit == "SELL" :
                            
                            if lp_value < entry_lp :
                                    
                                profit_loss = "PROFIT"
                                PT = lp_value - entry_lp
                                pro = PT * qty
                                TRADE_PNL = pro

                            elif lp_value > entry_lp :
                                profit_loss = "LOSS"   
                                PT = entry_lp - lp_value
                                pro = PT * qty
                                TRADE_PNL = -pro     
                            else:
                                profit_loss = "CTC"
                                PT = lp_value - entry_lp
                                pro = PT * qty
                                TRADE_PNL = pro             
                        
                        else:

                                profit_loss = "NO ENTRY NOT BUY OR SELL"
                                PT = 0
                                pro = 0
                                TRADE_PNL = 0

                        print(f"Placing exit order for {main_symbol} - symbol: {symbol}, qty: {opposite_qty} lp value {lp_value}")
        
                        update_data = pd.DataFrame({
                            'order_id':[order_id],
                            'Date': pd.Timestamp.now(),
                            'Symbol': [symbol],
                            'token_value' : [token_value],
                            'main_symbol': [main_symbol],
                            'Option_Type': [Option_Type],
                            'Qty': [opposite_qty],
                            'option_lp': [lp_value],
                            'BUY_sell_exit': ["EXIT"],
                            "exchange_value":["NFO"],
                            "TRADE_PNL":[TRADE_PNL],
                            'profit_or_loss' : [profit_loss],
                            "reason":[reason]
                        })

                        update_data.to_csv('PAPER_TRADE.csv', mode='a', header=False, index=False)

                        if live_trade :
                            qty =opposite_qty
                            symbol = symbol
                                 
                            inside_order_live(api=api,quantity=qty,product_type='MKT',exchange="NFO",symbol=symbol)
                    else:
                        print("lp is none not appending data contact devloper 7014403338 RASH_ALGO") 
                     
    else :
        print("Data not found. Passing None. kindly exit position if any ")



def exit_position_single(api,live_trade,exit_symbol,exit_order_id,reason):
    total_qty_sum_ce,total_qty_sum_pe,total_open_qty,symbol_open_qty,symbol_sum_qty_df,total_option_data_df,df_test,OPEN_DF,ce_filtered_df,pe_filtered_df =  data_per_csv(selected_symbol=None)
    df_csv = OPEN_DF
    print(OPEN_DF)
    if df_csv is not None :
            
        open_position_df = df_csv
        for index, row in open_position_df.iterrows():
            print(row)
            order_id = row['order_id']
            main_symbol = row['main_symbol']
            symbol = row['Symbol']
            qty = row['Qty']  
            Option_Type = row["Option_Type"] 
            exchange_value = row['exchange_value']
            entry_lp = row['option_lp']
            BUY_sell_exit = row['BUY_sell_exit']
            token_value = str(row['token_value_x'])
            traded_date = row['Date']


            if qty != 0 and symbol == exit_symbol  and order_id == exit_order_id:

    
                if qty != 0:
                    # Determine the opposite quantity and symbol
                    opposite_qty = -qty
    
                    lp_value=ltp(api,exchange_value,token_value)

                    if lp_value is not None:
                        if BUY_sell_exit == "BUY":
                            if lp_value > entry_lp :
                                    
                                profit_loss = "PROFIT"
                                PT = lp_value - entry_lp
                                pro = PT * qty
                                TRADE_PNL = pro
                            elif lp_value < entry_lp :
                                profit_loss = "LOSS"   
                                PT = entry_lp - lp_value
                                pro = PT * qty
                                TRADE_PNL = -pro     
                            else:
                                profit_loss = "CTC"
                                PT = lp_value - entry_lp
                                pro = PT * qty
                                TRADE_PNL = pro

                        elif BUY_sell_exit == "SELL" :
                            
                            if lp_value < entry_lp :
                                    
                                profit_loss = "PROFIT"
                                PT = lp_value - entry_lp
                                pro = PT * qty
                                TRADE_PNL = pro

                            elif lp_value > entry_lp :
                                profit_loss = "LOSS"   
                                PT = entry_lp - lp_value
                                pro = PT * qty
                                TRADE_PNL = -pro     
                            else:
                                profit_loss = "CTC"
                                PT = lp_value - entry_lp
                                pro = PT * qty
                                TRADE_PNL = pro             
                        
                        else:

                                profit_loss = "NO ENTRY NOT BUY OR SELL"
                                PT = 0
                                pro = 0
                                TRADE_PNL = 0

                        print(f"Placing exit order for {main_symbol} - symbol: {symbol}, qty: {opposite_qty} lp value {lp_value}")
        
                        update_data = pd.DataFrame({
                            'order_id':[order_id],
                            'Date': pd.Timestamp.now(),
                            "traded_date" : [traded_date],
                            'Symbol': [symbol],
                            'token_value' : [token_value],
                            'main_symbol': [main_symbol],
                            'Option_Type': [Option_Type],
                            'Qty': [opposite_qty],
                            'option_lp': [lp_value],
                            'BUY_sell_exit': ["EXIT"],
                            "exchange_value":["NFO"],
                            "TRADE_PNL":[TRADE_PNL],
                            'profit_or_loss' : [profit_loss],
                            "reason":[reason]
                        })

                        update_data.to_csv('PAPER_TRADE.csv', mode='a', header=False, index=False)

                        if live_trade :
                            qty =opposite_qty
                            symbol = symbol
                                 
                            inside_order_live(api=api,quantity=qty,product_type='MKT',exchange="NFO",symbol=symbol)
                    else:
                        print("lp is none not appending data contact devloper 7014403338 RASH_ALGO") 
                     
    else :
        print("Data not found. Passing None. kindly exit position if any ")






def exit_position_all_as_per_date(api,live_trade,reason) :
    total_qty_sum_ce,total_qty_sum_pe,total_open_qty,symbol_open_qty,symbol_sum_qty_df,total_option_data_df,df_test,OPEN_DF,ce_filtered_df,pe_filtered_df =  data_per_csv(selected_symbol=None)
    df_csv = OPEN_DF
    #print(OPEN_DF)

    df_csv['Date'] = pd.to_datetime(df_csv['Date'])
    from datetime import datetime 
    today_date = datetime.today().date()

    filtered_df = df_csv[df_csv['Date'].dt.date != today_date]
    #print(filtered_df)
    df_csv = filtered_df

    if df_csv is not None :

        # today_date = datetime.today().strftime('%Y-%m-%d')    
        open_position_df = df_csv
        for index, row in open_position_df.iterrows():
            print(row)
            order_id = row['order_id']
            main_symbol = row['main_symbol']
            symbol = row['Symbol']
            qty = row['Qty']  
            Option_Type = row["Option_Type"] 
            exchange_value = row['exchange_value']
            entry_lp = row['option_lp']
            BUY_sell_exit = row['BUY_sell_exit']
            Date = row['Date']
       

            token_value = str(row['token_value_x'])

            if qty != 0 and symbol == symbol :

    
                if qty != 0:
                    # Determine the opposite quantity and symbol
                    opposite_qty = -qty
    
                    lp_value=ltp(api,exchange_value,token_value)

                    if lp_value is not None:
                        if BUY_sell_exit == "BUY":
                            if lp_value > entry_lp :
                                    
                                profit_loss = "PROFIT"
                                PT = lp_value - entry_lp
                                pro = PT * qty
                                TRADE_PNL = pro
                            elif lp_value < entry_lp :
                                profit_loss = "LOSS"   
                                PT = entry_lp - lp_value
                                pro = PT * qty
                                TRADE_PNL = -pro     
                            else:
                                profit_loss = "CTC"
                                PT = lp_value - entry_lp
                                pro = PT * qty
                                TRADE_PNL = pro

                        elif BUY_sell_exit == "SELL" :
                            
                            if lp_value < entry_lp :
                                    
                                profit_loss = "PROFIT"
                                PT = lp_value - entry_lp
                                pro = PT * qty
                                TRADE_PNL = pro

                            elif lp_value > entry_lp :
                                profit_loss = "LOSS"   
                                PT = entry_lp - lp_value
                                pro = PT * qty
                                TRADE_PNL = -pro     
                            else:
                                profit_loss = "CTC"
                                PT = lp_value - entry_lp
                                pro = PT * qty
                                TRADE_PNL = pro             
                        
                        else:

                                profit_loss = "NO ENTRY NOT BUY OR SELL"
                                PT = 0
                                pro = 0
                                TRADE_PNL = 0

                        print(f"Placing exit order for {main_symbol} - symbol: {symbol}, qty: {opposite_qty} lp value {lp_value}")
        
                        update_data = pd.DataFrame({
                            'order_id':[order_id],
                            'Date': pd.Timestamp.now(),
                            'Symbol': [symbol],
                            'token_value' : [token_value],
                            'main_symbol': [main_symbol],
                            'Option_Type': [Option_Type],
                            'Qty': [opposite_qty],
                            'option_lp': [lp_value],
                            'BUY_sell_exit': ["EXIT"],
                            "exchange_value":["NFO"],
                            "TRADE_PNL":[TRADE_PNL],
                            'profit_or_loss' : [profit_loss],
                            "reason":[reason]
                        })

                        update_data.to_csv('PAPER_TRADE.csv', mode='a', header=False, index=False)

                        if live_trade :
                            qty =opposite_qty
                            symbol = symbol
                                 
                            inside_order_live(api=api,quantity=qty,product_type='MKT',exchange="NFO",symbol=symbol)
                    else:
                        print("lp is none not appending data contact devloper 7014403338 RASH_ALGO") 
                     
    else :
        print("Data not found. Passing None. kindly exit position if any ")
