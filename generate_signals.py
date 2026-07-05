import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import yaml
from datetime import datetime, timedelta

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def run_daily_logic():
    config = load_config()
    tickers = list(config["tickers"].values())
    names = list(config["tickers"].keys())
    
    # Fetch 250 days to ensure enough data for ROC(126)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=250)
    
    print(f"Fetching latest data for {tickers}...")
    df = yf.download(tickers, start=start_date, end=end_date)
    if df.empty:
        print("Failed to download data.")
        return
        
    dfs = {}
    for name, ticker in zip(names, tickers):
        try:
            ticker_df = df.xs(ticker, axis=1, level=1, drop_level=True)
            if ticker_df.index.tz is not None:
                ticker_df.index = ticker_df.index.tz_convert(None)
            dfs[name] = ticker_df
        except Exception as e:
            print(f"Error extracting {ticker}: {e}")
            return
            
    trading_dates = dfs['nifty'].index
    for name in names:
        dfs[name] = dfs[name].reindex(trading_dates).ffill()
        
    # Liquid BeES synthetic close
    liquid = dfs['liquid']
    daily_yield = 0.055 / 252
    liquid_synthetic_close = 1000 * (1 + daily_yield) ** np.arange(len(liquid))
    liquid['Close'] = liquid_synthetic_close
    dfs['liquid'] = liquid
    
    close = pd.DataFrame({n: dfs[n]['Close'] for n in names})
    high = pd.DataFrame({n: dfs[n]['High'] for n in names})
    low = pd.DataFrame({n: dfs[n]['Low'] for n in names})
    
    ema20 = close.apply(lambda x: ta.ema(x, length=20))
    sma50 = close.apply(lambda x: ta.sma(x, length=50))
    rsi14 = close.apply(lambda x: ta.rsi(x, length=14))
    roc126 = close.apply(lambda x: ta.roc(x, length=126))
    
    def get_macd_line(x):
        res = ta.macd(x, fast=12, slow=26, signal=9)
        return res.iloc[:, 0] if res is not None and not res.empty else pd.Series(index=x.index, dtype=float)
        
    def get_macd_signal(x):
        res = ta.macd(x, fast=12, slow=26, signal=9)
        return res.iloc[:, 2] if res is not None and not res.empty else pd.Series(index=x.index, dtype=float)

    macd_line = close.apply(get_macd_line)
    macd_signal = close.apply(get_macd_signal)
    
    latest_roc126 = roc126.iloc[-1]
    max_roc_asset = latest_roc126.idxmax()
    active_asset = {n: (n == max_roc_asset) for n in names}
    
    print("\n--- Current Market State ---")
    print(f"Date: {trading_dates[-1].date()}")
    print(f"Active Asset (Macro Regime): {max_roc_asset.upper()}")
    print("Latest 6m ROC:")
    print(latest_roc126)
    
    print("\n--- Swing Execution Logic ---")
    latest_close = close.iloc[-1]
    latest_high = high.iloc[-1]
    latest_low = low.iloc[-1]
    latest_ema20 = ema20.iloc[-1]
    latest_rsi14 = rsi14.iloc[-1]
    
    for asset in ["nifty", "gold"]:
        if active_asset[asset]:
            print(f"{asset.upper()} is active.")
            is_pullback = (latest_low[asset] <= latest_ema20[asset]) and (latest_high[asset] >= latest_ema20[asset])
            is_proximity = (latest_close[asset] <= latest_ema20[asset] * 1.015) and (latest_close[asset] >= latest_ema20[asset] * 0.985)
            is_rsi_ok = (latest_rsi14[asset] > 40) and (latest_rsi14[asset] < 70)
            
            print(f"  Pullback/Proximity to EMA20 ({latest_ema20[asset]:.2f}): {is_pullback or is_proximity}")
            print(f"  RSI(14) between 40-70 ({latest_rsi14[asset]:.2f}): {is_rsi_ok}")
            
            if (is_pullback or is_proximity) and is_rsi_ok:
                print(f"  >> BUY SIGNAL for {asset.upper()}")
            else:
                print(f"  >> NO ENTRY SIGNAL for {asset.upper()} today.")
                
    if active_asset["liquid"]:
        print("LIQUID is active. >> HOLD CASH (Liquid BeES)")
        
    print("\n--- Exit Triggers Check ---")
    for asset in ["nifty", "gold"]:
        cross_below = (macd_line[asset].iloc[-1] < macd_signal[asset].iloc[-1]) and (macd_line[asset].iloc[-2] >= macd_signal[asset].iloc[-2])
        close_below_sma = latest_close[asset] < sma50[asset].iloc[-1]
        not_active = not active_asset[asset]
        
        print(f"{asset.upper()}:")
        print(f"  MACD Bearish Cross: {cross_below}")
        print(f"  Close below 50 SMA: {close_below_sma}")
        print(f"  Regime Shift (Not Active): {not_active}")
        
        if cross_below or close_below_sma or not_active:
            print(f"  >> SELL SIGNAL for {asset.upper()} (If currently held)")
        else:
            print(f"  >> NO SELL SIGNAL for {asset.upper()} (Hold if in position)")

if __name__ == "__main__":
    run_daily_logic()
