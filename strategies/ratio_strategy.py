import yfinance as yf
import pandas as pd
import numpy as np

def load_data(data_dir=None):
    # Fetch 5 years to match exploration
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*5)
    tickers = ["NIFTYBEES.NS", "GOLDBEES.NS"]
    
    df = yf.download(tickers, start=start_date, end=end_date, auto_adjust=True, progress=False)
    if 'Close' in df.columns:
        df = df['Close']
    else:
        df = df.xs('Close', axis=1, level=0)
        
    df = df.ffill().dropna()
    return {'close': df}

def generate_signals(data):
    df = data['close']
    nifty = df["NIFTYBEES.NS"]
    gold = df["GOLDBEES.NS"]
    
    ratio = nifty / gold
    sma50 = ratio.rolling(50).mean()
    sma200 = ratio.rolling(200).mean()
    
    # We allocate 100% to Nifty when true, else 100% to Gold
    entries = pd.DataFrame(index=df.index, columns=df.columns)
    entries["NIFTYBEES.NS"] = np.where((sma50 > sma200) & (sma50.shift(1) <= sma200.shift(1)), True, False)
    entries["GOLDBEES.NS"] = np.where((sma50 < sma200) & (sma50.shift(1) >= sma200.shift(1)), True, False)
    
    exits = pd.DataFrame(index=df.index, columns=df.columns)
    exits["NIFTYBEES.NS"] = np.where((sma50 < sma200) & (sma50.shift(1) >= sma200.shift(1)), True, False)
    exits["GOLDBEES.NS"] = np.where((sma50 > sma200) & (sma50.shift(1) <= sma200.shift(1)), True, False)
    
    # Add initial trade
    if len(sma50.dropna()) > 0:
        first_valid_idx = sma200.first_valid_index()
        is_nifty_bull = sma50.loc[first_valid_idx] > sma200.loc[first_valid_idx]
        entries.loc[first_valid_idx, "NIFTYBEES.NS"] = is_nifty_bull
        entries.loc[first_valid_idx, "GOLDBEES.NS"] = not is_nifty_bull
    
    return entries, exits, df
