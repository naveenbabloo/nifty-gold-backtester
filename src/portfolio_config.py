import vectorbt as vbt
import yaml

def create_portfolio(close, entries, exits):
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
        
    capital = config["capital"]
    slippage = config["slippage"]
    # For a flat fee of 20 INR, it's easier to approximate it as a percentage for backtesting 
    # if using standard from_signals. Assuming average trade size is full capital, 20 / 1000000 = 0.00002
    pct_fee = config["fees"] / capital
    
    # 5% trailing stop loss as requested
    pf = vbt.Portfolio.from_signals(
        close,
        entries,
        exits,
        init_cash=capital,
        fees=pct_fee,
        slippage=slippage,
        freq="1D",
        sl_stop=0.05,
        sl_trail=True,
        cash_sharing=True,
        group_by=True
    )
    return pf
