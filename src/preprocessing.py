import pandas as pd
import numpy as np
import os

def process_data():
    data_dir = "data"
    
    # Load data
    try:
        nifty = pd.read_csv(os.path.join(data_dir, "nifty.csv"), index_col="Date", parse_dates=True)
        gold = pd.read_csv(os.path.join(data_dir, "gold.csv"), index_col="Date", parse_dates=True)
        liquid = pd.read_csv(os.path.join(data_dir, "liquid.csv"), index_col="Date", parse_dates=True)
    except FileNotFoundError as e:
        print(f"Data files not found: {e}. Please run data_ingestion.py first.")
        return

    # Keep only the timezone-naive date if it has timezone info to avoid matching issues
    for df in [nifty, gold, liquid]:
        if df.index.tz is not None:
            df.index = df.index.tz_convert(None)

    # Align dates and forward fill
    # We will use Nifty's index as the primary trading calendar
    trading_dates = nifty.index
    
    nifty = nifty.reindex(trading_dates).ffill()
    gold = gold.reindex(trading_dates).ffill()
    liquid = liquid.reindex(trading_dates).ffill()
    
    # Liquid BeES Special Handling
    # The NAV is generally fixed at 1000. The return comes from daily fractional units (dividend).
    # Since yfinance dividend data for Indian ETFs can be spotty, we'll model an annualized 
    # yield of ~5.5% distributed evenly across trading days to calculate a synthetic cumulative return index.
    
    annual_yield = 0.055
    trading_days_per_year = 252
    daily_yield = annual_yield / trading_days_per_year
    
    # Create a synthetic closing price representing the cumulative value of 1 unit
    liquid_synthetic_close = 1000 * (1 + daily_yield) ** np.arange(len(liquid))
    liquid['Close'] = liquid_synthetic_close
    # Update other columns to be consistent
    liquid['Open'] = liquid_synthetic_close
    liquid['High'] = liquid_synthetic_close
    liquid['Low'] = liquid_synthetic_close
    liquid['Adj Close'] = liquid_synthetic_close
    
    # Save processed data
    nifty.to_csv(os.path.join(data_dir, "nifty_clean.csv"))
    gold.to_csv(os.path.join(data_dir, "gold_clean.csv"))
    liquid.to_csv(os.path.join(data_dir, "liquid_clean.csv"))
    
    print("Data preprocessing and Liquid BeES special handling complete.")

if __name__ == "__main__":
    process_data()
