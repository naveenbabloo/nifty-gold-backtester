import sys
sys.path.append('.')
import vectorbt as vbt
import pandas as pd
import numpy as np
from strategies.dual_momentum_swing import load_data, generate_signals
from src.portfolio_config import create_portfolio
from src.tax_tracker import apply_taxes

def run():
    print("Loading data and generating signals...")
    data = load_data('data')
    entries, exits, _ = generate_signals(data)
    
    print("Creating Portfolio...")
    portfolio = create_portfolio(data['close'], entries, exits)
    
    print("\n--- Pre-Tax Portfolio Stats ---")
    stats = portfolio.stats()
    print(f"Total Return: {stats['Total Return [%]']:.2f}%")
    print(f"Max Drawdown: {stats['Max Drawdown [%]']:.2f}%")
    print(f"Win Rate: {stats['Win Rate [%]']:.2f}%")
    
    print("\n--- Tax & Fees Impact ---")
    # Apply taxes
    trades_with_tax = apply_taxes(portfolio)
    
    if len(trades_with_tax) > 0:
        total_pre_tax = trades_with_tax['PnL'].sum()
        total_tax = trades_with_tax['Tax Paid'].sum()
        total_post_tax = trades_with_tax['Post-Tax PnL'].sum()
        
        init_cash = portfolio.init_cash
        if hasattr(init_cash, 'iloc'):
            init_cash = float(init_cash.iloc[0])
        elif isinstance(init_cash, (list, np.ndarray)):
            init_cash = float(init_cash[0])
        else:
            init_cash = float(init_cash)
            
        final_value_pre_tax = init_cash + total_pre_tax
        final_value_post_tax = init_cash + total_post_tax
        
        total_return_post_tax = (total_post_tax / init_cash) * 100
        
        print(f"\nInitial Capital: ₹{init_cash:,.2f}")
        print(f"Total Trades: {len(trades_with_tax)}")
        print(f"Pre-Tax Final Value: ₹{final_value_pre_tax:,.2f}")
        print(f"Tax Paid: ₹{total_tax:,.2f}")
        print(f"Post-Tax Final Value: ₹{final_value_post_tax:,.2f}")
        print(f"Post-Tax Total Return: {total_return_post_tax:.2f}%")
    else:
        print("No trades were made.")

if __name__ == "__main__":
    run()
