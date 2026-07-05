import yfinance as yf
import yaml
import os
import pandas as pd
from datetime import datetime, timedelta

def load_config(config_path="config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def download_data(years=10):
    config = load_config()
    tickers = list(config.get("tickers", {}).values())
    names = list(config.get("tickers", {}).keys())
    
    if not tickers:
        print("No tickers found in config.")
        return

    # Download data for all tickers at once (yfinance supports this)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    
    os.makedirs("data", exist_ok=True)
    
    print(f"Downloading data for: {tickers}")
    df = yf.download(tickers, start=start_date, end=end_date)
    
    if df.empty:
        print("Failed to download data.")
        return
        
    # Save individual CSVs
    for name, ticker in zip(names, tickers):
        # yfinance multi-ticker download results in a MultiIndex column
        try:
            ticker_df = df.xs(ticker, axis=1, level=1, drop_level=True)
            filepath = os.path.join("data", f"{name}.csv")
            ticker_df.to_csv(filepath)
            print(f"Saved {name} data to {filepath}")
        except Exception as e:
            print(f"Error saving {ticker}: {e}")

if __name__ == "__main__":
    download_data()
