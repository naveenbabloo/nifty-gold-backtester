import yfinance as yf
import pandas as pd
import numpy as np
import vectorbt as vbt
from datetime import datetime, timedelta

def run_ratio_backtests():
    # 1. Fetch Data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*5) # 5 years
    tickers = ["NIFTYBEES.NS", "GOLDBEES.NS"]
    
    print("Fetching 10 years of data...")
    df = yf.download(tickers, start=start_date, end=end_date, auto_adjust=True, progress=False)
    if 'Close' in df.columns:
        df = df['Close']
    else:
        df = df.xs('Close', axis=1, level=0)
    
    df = df.ffill().dropna()
    
    nifty = df["NIFTYBEES.NS"]
    gold = df["GOLDBEES.NS"]
    
    # 2. Calculate Ratio and MAs
    ratio = nifty / gold
    sma50 = ratio.rolling(50).mean()
    sma200 = ratio.rolling(200).mean()
    
    # 3. Strategy 1: Pure Ratio (No Crash Filter)
    target_weights = pd.DataFrame(index=df.index, columns=["NIFTYBEES.NS", "GOLDBEES.NS"])
    target_weights["NIFTYBEES.NS"] = np.where(sma50 > sma200, 1.0, 0.0)
    target_weights["GOLDBEES.NS"] = np.where(sma50 <= sma200, 1.0, 0.0)
    
    pf1 = vbt.Portfolio.from_orders(
        close=df,
        size=target_weights,
        size_type='targetpercent',
        group_by=True,
        cash_sharing=True,
        init_cash=100000,
        fees=0.002, # 0.2% combined slippage/brokerage
        freq='1D'
    )
    
    # 4. Strategy 2: Ratio + Crash Filter
    nifty_sma200 = nifty.rolling(200).mean()
    gold_sma200 = gold.rolling(200).mean()
    
    # If both assets are below their 200 SMA, it's a crash. We hold 0 of both (Cash)
    crash_condition = (nifty < nifty_sma200) & (gold < gold_sma200)
    
    target_weights_2 = target_weights.copy()
    target_weights_2.loc[crash_condition, "NIFTYBEES.NS"] = 0.0
    target_weights_2.loc[crash_condition, "GOLDBEES.NS"] = 0.0
    
    pf2 = vbt.Portfolio.from_orders(
        close=df,
        size=target_weights_2,
        size_type='targetpercent',
        group_by=True,
        cash_sharing=True,
        init_cash=100000,
        fees=0.002,
        freq='1D'
    )
    
    print("\n=== STRATEGY 1: Pure Ratio Switching ===")
    print(f"Total Return: {pf1.total_return() * 100:.2f}%")
    print(f"Max Drawdown: {pf1.max_drawdown() * 100:.2f}%")
    print(f"Win Rate: {pf1.trades.winning.count() / max(1, pf1.trades.count()) * 100:.2f}%")
    print(f"Total Trades: {pf1.trades.count()}")
    
    print("\n=== STRATEGY 2: Ratio + Crash Filter (Cash) ===")
    print(f"Total Return: {pf2.total_return() * 100:.2f}%")
    print(f"Max Drawdown: {pf2.max_drawdown() * 100:.2f}%")
    print(f"Win Rate: {pf2.trades.winning.count() / max(1, pf2.trades.count()) * 100:.2f}%")
    print(f"Total Trades: {pf2.trades.count()}")

if __name__ == "__main__":
    run_ratio_backtests()
