import yfinance as yf
import pandas as pd
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
    
    # We only care about Nifty and Gold for Strategy 1
    # LiquidBeES is ignored
    core_tickers = ["NIFTYBEES.NS", "GOLDBEES.NS"]
    
    # Fetch 300 days to ensure enough data for 200 SMA
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    df = yf.download(core_tickers, start=start_date, end=end_date, auto_adjust=True, progress=False)
    if 'Close' in df.columns:
        df = df['Close']
    else:
        df = df.xs('Close', axis=1, level=0)
        
    df = df.ffill().dropna()
    
    if df.empty:
        return {"error": "Failed to download data."}
        
    nifty = df["NIFTYBEES.NS"]
    gold = df["GOLDBEES.NS"]
    
    # Calculate Ratio and MAs
    ratio = nifty / gold
    sma50 = ratio.rolling(50).mean()
    sma200 = ratio.rolling(200).mean()
    
    # Get latest values
    latest_ratio = ratio.iloc[-1]
    latest_sma50 = sma50.iloc[-1]
    latest_sma200 = sma200.iloc[-1]
    
    # Logic: if SMA50 > SMA200, Nifty is active. Else Gold is active.
    is_nifty_bull = latest_sma50 > latest_sma200
    active_asset = "nifty" if is_nifty_bull else "gold"
    
    results = {
        "date": df.index[-1].date().isoformat(),
        "active_asset": active_asset,
        "ratio_metrics": {
            "current_ratio": float(latest_ratio),
            "sma50": float(latest_sma50) if not np.isnan(latest_sma50) else None,
            "sma200": float(latest_sma200) if not np.isnan(latest_sma200) else None
        },
        "signals": {},
        "chart_data": {}
    }
    
    # Signals
    results["signals"]["nifty"] = {
        "action": "BUY" if is_nifty_bull else "SELL",
        "reason": "Ratio 50 SMA > 200 SMA (Nifty Outperforming)" if is_nifty_bull else "Ratio 50 SMA < 200 SMA (Gold Outperforming)",
        "color": "green" if is_nifty_bull else "red"
    }
    
    results["signals"]["gold"] = {
        "action": "SELL" if is_nifty_bull else "BUY",
        "reason": "Ratio 50 SMA > 200 SMA (Nifty Outperforming)" if is_nifty_bull else "Ratio 50 SMA < 200 SMA (Gold Outperforming)",
        "color": "red" if is_nifty_bull else "green"
    }
    
    # Provide chart data for the Ratio (last 250 days)
    chart_df = pd.DataFrame({
        "Ratio": ratio.tail(250),
        "SMA50": sma50.tail(250),
        "SMA200": sma200.tail(250)
    })
    
    chart_df.index = chart_df.index.strftime('%Y-%m-%d')
    chart_df_reset = chart_df.reset_index().rename(columns={'Date': 'Date'})
    # Fix the index column name from 'index' to 'Date'
    chart_df_reset.rename(columns={'index': 'Date'}, inplace=True)
    
    # Fill NaNs with None for JSON serialization
    chart_df_reset = chart_df_reset.replace({np.nan: None})
    
    results["chart_data"]["ratio"] = chart_df_reset.to_dict(orient="records")
    
    return results

if __name__ == "__main__":
    import json
    print(json.dumps(run_daily_logic(), indent=2))
