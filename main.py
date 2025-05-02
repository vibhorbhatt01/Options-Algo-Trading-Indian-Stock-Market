from strategy_helper import *
from paper_trade import *
import asyncio
import traceback
import logging

start_time = "02:20"             # Define your start time
end_time = "05:45"               # Define your end time
script_stop_time = "06:00"  



MAIN_SL =  # in per 
MAIN_TG =   #  in per 
START_TRALING = 1500
TRAIL_MINUS_POINTS = 
qty = -15  # - S FOR SELLIMNG + BUY 
atm_diff = 2 #  2 is for otm  -2 then itm  0 its for atm 
strike_gap = 100


MAIN_SYMBOL = "BANKNIFTY"  # BANKNIFTY NIFTY 
SERCH_SYMBOL = "NIFTY BANK" # BANKNIFTY (NIFTY BANK)
month = "MAY" 

live_trade = False # false then paper True paper and live 


logging.basicConfig(filename='trading.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info(f"main file run started")
def order_place_starting(SERCH_SYMBOL, optt, strike, strike_gap):
    ORDER_PLACED_TODAY = check_trade_data(main_symbol=MAIN_SYMBOL, option_type=optt)
    if ORDER_PLACED_TODAY == 0:
        spot_token, spot_tsym, spot_exch = get_symbol(api, SERCH_SYMBOL)
        tysm_value, token_value, exchange_value = exchange_valuestrike_selection(
            api=api, serchsym=spot_tsym, token_value=spot_token, 
            exchange_value=spot_exch, strike_gap=strike_gap, 
            strike=strike, month=month, optt=optt
        )
        
        logging.info(f"Placing order: tysm_value={tysm_value}, token_value={token_value}, exchange_value={exchange_value}")
        place_order(api=api, symbol=tysm_value, token_value=token_value, 
                    main_symbol=MAIN_SYMBOL, qty=qty, optt=optt, 
                    live_trade=live_trade, reason="START ORDER")
    else:
        logging.info(f"Order already placed for {MAIN_SYMBOL} option type is {optt}")

def inside_sell_and_buy_sl(order_id, buy_sell_exit, option_lp, current_lp, symbol):
    logging.info(f"Checking SL/TP for {buy_sell_exit} order: symbol={symbol}, order_id={order_id}, option_lp={option_lp}, current_lp={current_lp}")
    option_sl = (MAIN_SL / 100) * option_lp
    option_tg = (MAIN_TG / 100) * option_lp
    
    if buy_sell_exit == "BUY":
        BUY_sl = option_lp - option_sl
        BUY_tg = option_lp + option_tg
        if current_lp < BUY_sl:
            logging.info(f"BUY SL hit: symbol={symbol}, BUY_sl={BUY_sl}, current_lp={current_lp}, traded price={option_lp}")
            exit_position_single(api=api, live_trade=live_trade, exit_symbol=symbol, exit_order_id=order_id, reason=f"BUY SL hit: symbol={symbol}, BUY_sl={BUY_sl}, current_lp={current_lp}, traded price={option_lp}")
        elif current_lp > BUY_tg:
            logging.info(f"BUY TP hit: symbol={symbol}, BUY_tg={BUY_tg}, current_lp={current_lp}, traded price={option_lp}")
            exit_position_single(api=api, live_trade=live_trade, exit_symbol=symbol, exit_order_id=order_id, reason=f"BUY TP hit: symbol={symbol}, BUY_tg={BUY_tg}, current_lp={current_lp}, traded price={option_lp}")
        else:
            logging.info("Nothing hit in buy side")
    
    elif buy_sell_exit == "SELL":
        SELL_sl = option_lp + option_sl
        SELL_tg = option_lp - option_tg
        if current_lp > SELL_sl:
            logging.info(f"SELL SL hit: symbol={symbol}, SELL_sl={SELL_sl}, current_lp={current_lp}, traded price={option_lp}")
            exit_position_single(api=api, live_trade=live_trade, exit_symbol=symbol, exit_order_id=order_id, reason=f"SELL SL hit: symbol={symbol}, SELL_sl={SELL_sl}, current_lp={current_lp}, traded price={option_lp}")
        elif current_lp < SELL_tg:
            logging.info(f"SELL TP hit: symbol={symbol}, SELL_tg={SELL_tg}, current_lp={current_lp}, traded price={option_lp}")
            exit_position_single(api=api, live_trade=live_trade, exit_symbol=symbol, exit_order_id=order_id, reason=f"SELL TP hit: symbol={symbol}, SELL_tg={SELL_tg}, current_lp={current_lp}, traded price={option_lp}")
        else:
            logging.info("Nothing hit in sell side")
    else:
        logging.info("SL condition not checked: buy_sell_exit not in expected values")

def pnl_base_exit(total_pnl_exit_plus_close, total_current_pnl, symbol, date, exit_order_id):
    logging.info(f"Checking PnL-based exit: symbol={symbol}, total_pnl_exit_plus_close={total_pnl_exit_plus_close}, total_current_pnl={total_current_pnl}, date={date}")
    if total_pnl_exit_plus_close > START_TRALING:
        last_exit_pnl = total_pnl_exit_plus_close - TRAIL_MINUS_POINTS
        if total_current_pnl < last_exit_pnl:
            logging.info(f"Trail SL hit: symbol={symbol}, total_current_pnl={total_current_pnl}, last_exit_pnl={last_exit_pnl}, date={date}")
            exit_position_single(api=api, live_trade=live_trade, exit_symbol=symbol, exit_order_id=exit_order_id, reason=f"Trail SL hit: symbol={symbol}, total_current_pnl={total_current_pnl}, last_exit_pnl={last_exit_pnl}, date={date}")
        else:
            logging.info(f"Trail SL checked: symbol={symbol}, total_current_pnl={total_current_pnl}, last_exit_pnl={last_exit_pnl}, total_pnl_exit_plus_close={total_pnl_exit_plus_close}, date={date}")

def exit_when_sl_and_pnl_hit():
    result_df = append_open_ltp_pnl_to_csv()
    
    if result_df is not None:
        logging.info("DataFrame returned from the function:")
        for index, row in result_df.iterrows():
            order_id = row['order_id']
            symbol = row['Symbol']
            token_value_x = row['token_value_x']
            main_symbol = row['main_symbol']
            option_type = row['Option_Type']
            exchange_value = row['exchange_value']
            qty = row['Qty']
            token_value_y = row['token_value_y']
            date = row['Date']
            option_lp = row['option_lp']
            buy_sell_exit = row['BUY_sell_exit']
            pnl = row['pnl']
            current_lp = row['current_lp']
            max_pnl = row['max_pnl']
            min_pnl = row['min_pnl']
            date_only = row['Date_only']
            total_current_pnl = row['total_current_pnl']
            exit_total_pnl = row['exit_total_pnl']
            total_pnl_exit_plus_close = row['total_pnl_exit_plus_close']

            logging.info(f"Order ID: {order_id}")
            logging.info(f"Symbol: {symbol}")
            logging.info(f"Token Value X: {token_value_x}")
            logging.info(f"Main Symbol: {main_symbol}")
            logging.info(f"Option Type: {option_type}")
            logging.info(f"Exchange Value: {exchange_value}")
            logging.info(f"Qty: {qty}")
            logging.info(f"Token Value Y: {token_value_y}")
            logging.info(f"Date: {date}")
            logging.info(f"Option LP: {option_lp}")
            logging.info(f"BUY/SELL/EXIT: {buy_sell_exit}")
            logging.info(f"PNL: {pnl}")
            logging.info(f"Current LP: {current_lp}")
            logging.info(f"Max PNL: {max_pnl}")
            logging.info(f"Min PNL: {min_pnl}")
            logging.info(f"Date Only: {date_only}")
            logging.info(f"Total Current PNL: {total_current_pnl}")
            logging.info(f"Exit Total PNL: {exit_total_pnl}")
            logging.info(f"Total PNL (max_pnl + Close): {total_pnl_exit_plus_close}")

            inside_sell_and_buy_sl(
                order_id=order_id,
                buy_sell_exit=buy_sell_exit,
                option_lp=option_lp,
                current_lp=current_lp,
                symbol=symbol
            )
            pnl_base_exit(
                total_pnl_exit_plus_close=total_pnl_exit_plus_close,
                total_current_pnl=total_current_pnl,
                symbol=symbol,
                date=date,
                exit_order_id=order_id
            )
    else:
        logging.info("No data to process. The DataFrame is empty.")
        print("No data to process. The DataFrame is empty.")


def place_market_strat ():
    now = datetime.now()
    current_time = now.time()
    ddt = datetime.strptime(start_time, "%H:%M").time()

    if  current_time >= datetime.strptime(start_time, "%H:%M").time() :
        print("placing order  place_market_strat () ")
        order_place_starting(SERCH_SYMBOL,"PE",atm_diff,strike_gap)  
        order_place_starting(SERCH_SYMBOL,"CE",atm_diff,strike_gap)    

    else:
        print("check condition not satisfy place_market_strat () ")    

async def EVERY_run():
    try:
        place_market_strat ()
        exit_when_sl_and_pnl_hit() 
    except Exception as e:
        print(f"An EVERY_run() e occurred no worries : {e}")
        traceback.print_exc()


async def main():
    now = datetime.now()
    current_time = now.time()
    print(f"Current time: {current_time}")


    # Run EVERY_run every 5 seconds until end_time
    while current_time < datetime.strptime(end_time, "%H:%M").time() and \
          current_time < datetime.strptime(end_time, "%H:%M").time():
        
        await EVERY_run()
        await asyncio.sleep(2)

        now = datetime.now()
        current_time = now.time()

    # Exit all orders and stop the script between end_time and script_stop_time
    if current_time >= datetime.strptime(end_time, "%H:%M").time() and \
       current_time < datetime.strptime(script_stop_time, "%H:%M").time():
        print("Exiting all orders... and stop script ")
        exit_position_all_as_per_date(api,live_trade,"exit on base of exit time is breached  ") 
        

if __name__ == "__main__":
    asyncio.run(main())

