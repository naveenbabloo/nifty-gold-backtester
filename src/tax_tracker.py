import numpy as np
import pandas as pd
from numba import njit
import yaml

@njit
def calculate_tax_drag(entry_times, exit_times, pnls, asset_types, equity_stcg, equity_ltcg, debt_stcg, debt_ltcg):
    """
    Numba-compiled function to calculate the tax on each trade and accumulate post-tax PnL.
    asset_types: 0 for Equity (Nifty), 1 for Debt/Gold (Gold, Liquid)
    entry_times, exit_times are in days (or just use timedelta > 365).
    """
    n = len(pnls)
    taxes = np.zeros(n)
    post_tax_pnl = np.zeros(n)
    
    for i in range(n):
        pnl = pnls[i]
        
        # Only pay tax on profits
        if pnl <= 0:
            taxes[i] = 0
            post_tax_pnl[i] = pnl
            continue
            
        holding_period_days = exit_times[i] - entry_times[i]
        is_long_term = holding_period_days > 365
        
        if asset_types[i] == 0:  # Equity
            tax_rate = equity_ltcg if is_long_term else equity_stcg
        else:  # Debt / Gold
            tax_rate = debt_ltcg if is_long_term else debt_stcg
            
        taxes[i] = pnl * tax_rate
        post_tax_pnl[i] = pnl - taxes[i]
        
    return taxes, post_tax_pnl

def apply_taxes(portfolio):
    """
    Post-process vectorbt Portfolio to calculate post-tax metrics.
    Note: This is an approximation as it doesn't reduce the reinvestable capital 
    during the backtest path itself. To do that requires a custom order_func.
    """
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
        
    tax_rates = config["tax_rates"]
    
    trades = portfolio.trades.records_readable
    
    # Need to map columns to arrays for Numba
    # 'Column' in vectorbt trades represents the asset name/index
    # Assuming 'nifty' is index 0 or we can map it by name
    
    # We will just print the tax summary for now
    if len(trades) == 0:
        return 0, 0
        
    entry_days = (trades['Entry Timestamp'] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1D')
    exit_days = (trades['Exit Timestamp'] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1D')
    pnls = trades['PnL'].values
    
    # Determine asset types from column
    # 0 = Equity, 1 = Debt/Gold
    asset_types = np.where(trades['Column'] == 'nifty', 0, 1)
    
    taxes, post_tax_pnls = calculate_tax_drag(
        entry_days.values, 
        exit_days.values, 
        pnls, 
        asset_types,
        tax_rates['equity_stcg'],
        tax_rates['equity_ltcg'],
        tax_rates['debt_stcg'],
        tax_rates['debt_ltcg']
    )
    
    trades_with_tax = trades.copy()
    trades_with_tax['Tax Paid'] = taxes
    trades_with_tax['Post-Tax PnL'] = post_tax_pnls
    
    total_pre_tax_pnl = np.sum(pnls)
    total_tax = np.sum(taxes)
    total_post_tax_pnl = np.sum(post_tax_pnls)
    
    print(f"Total Pre-Tax PnL: ₹{total_pre_tax_pnl:,.2f}")
    print(f"Total Tax Paid: ₹{total_tax:,.2f}")
    print(f"Total Post-Tax PnL: ₹{total_post_tax_pnl:,.2f}")
    
    return trades_with_tax
