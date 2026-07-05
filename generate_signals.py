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
    
    df = yf.download(tickers, start=start_date, end=end_date, progress=False)
    if df.empty:
        return {"error": "Failed to download data."}
        
    dfs = {}
    for name, ticker in zip(names, tickers):
        try:
            ticker_df = df.xs(ticker, axis=1, level=1, drop_level=True)
            if ticker_df.index.tz is not None:
                ticker_df.index = ticker_df.index.tz_convert(None)
            dfs[name] = ticker_df
        except Exception as e:
            return {"error": f"Error extracting {ticker}: {e}"}
            
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
    
    latest_close = close.iloc[-1]
    latest_high = high.iloc[-1]
    latest_low = low.iloc[-1]
    latest_ema20 = ema20.iloc[-1]
    latest_sma50 = sma50.iloc[-1]
    latest_rsi14 = rsi14.iloc[-1]
    
    results = {
        "date": trading_dates[-1].date().isoformat(),
        "active_asset": max_roc_asset,
        "roc": latest_roc126.to_dict(),
        "signals": {},
        "chart_data": {}
    }
    
    for asset in ["nifty", "gold"]:
        is_active = active_asset[asset]
        is_pullback = (latest_low[asset] <= latest_ema20[asset]) and (latest_high[asset] >= latest_ema20[asset])
        is_proximity = (latest_close[asset] <= latest_ema20[asset] * 1.015) and (latest_close[asset] >= latest_ema20[asset] * 0.985)
        is_rsi_ok = (latest_rsi14[asset] > 40) and (latest_rsi14[asset] < 70)
        
        cross_below = (macd_line[asset].iloc[-1] < macd_signal[asset].iloc[-1]) and (macd_line[asset].iloc[-2] >= macd_signal[asset].iloc[-2])
        close_below_sma = latest_close[asset] < latest_sma50[asset]
        
        action = "HOLD"
        reason = "No entry/exit conditions met."
        color = "blue"
        
        if not is_active:
            action = "SELL"
            reason = "Regime shift. Not the active asset."
            color = "red"
        elif cross_below or close_below_sma:
            action = "SELL"
            reason = f"Exit triggered: {'MACD Bearish Cross' if cross_below else 'Close below 50 SMA'}."
            color = "red"
        elif is_active and (is_pullback or is_proximity) and is_rsi_ok:
            action = "BUY"
            reason = "Active Asset + Pullback to EMA20 + RSI(14) between 40-70."
            color = "green"
        elif is_active:
            action = "HOLD"
            reason = "Active Asset. Waiting for pullback to 20 EMA."
            color = "yellow"
            
        results["signals"][asset] = {
            "action": action,
            "reason": reason,
            "color": color,
            "metrics": {
                "close": float(latest_close[asset]),
                "ema20": float(latest_ema20[asset]),
                "sma50": float(latest_sma50[asset]),
                "rsi14": float(latest_rsi14[asset]),
                "roc126": float(latest_roc126[asset])
            }
        }
        
        # Save last 60 days for charting
        chart_df = dfs[asset].tail(60).copy()
        chart_df['EMA20'] = ema20[asset].tail(60)
        chart_df['SMA50'] = sma50[asset].tail(60)
        
        # Convert to records for JSON serialization (Streamlit session state compatibility)
        chart_df.index = chart_df.index.strftime('%Y-%m-%d')
        chart_df_reset = chart_df.reset_index().rename(columns={'index': 'Date'})
        results["chart_data"][asset] = chart_df_reset.to_dict(orient="records")
        
    # Liquid
    results["signals"]["liquid"] = {
        "action": "BUY" if active_asset["liquid"] else "HOLD",
        "reason": "Market in cash regime." if active_asset["liquid"] else "Not in cash regime.",
        "color": "blue" if active_asset["liquid"] else "gray",
        "metrics": {
            "close": float(latest_close["liquid"]),
            "roc126": float(latest_roc126["liquid"])
        }
    }
    
    return results

if __name__ == "__main__":
    import json
    print(json.dumps(run_daily_logic(), indent=2))
