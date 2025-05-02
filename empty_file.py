from paper_trade import *
from strategy_helper import api
from main import live_trade

exit_position_all(api,live_trade,"empty file ") 

def empty_pnl_csv():
        
    total_qty_sum_ce,total_qty_sum_pe,total_open_qty,symbol_open_qty,symbol_sum_qty_df,total_option_data_df,df_test,OPEN_DF,ce_filtered_df,pe_filtered_df =  data_per_csv(selected_symbol=None)
    
    pnl_df = pd.read_csv("pnl.csv")
    
    opendf_order_ids = OPEN_DF['order_id'].tolist()
    filtered_pnl_df = pnl_df[pnl_df['orderid'].isin(opendf_order_ids)]
    filtered_pnl_df.to_csv('pnl.csv', index=False)
    print(filtered_pnl_df)
empty_pnl_csv()    