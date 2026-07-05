import pandas as pd
import pandas_ta as ta
import os

def generate_features():
    data_dir = "data"
    
    try:
        nifty = pd.read_csv(os.path.join(data_dir, "nifty_clean.csv"), index_col="Date", parse_dates=True)
        gold = pd.read_csv(os.path.join(data_dir, "gold_clean.csv"), index_col="Date", parse_dates=True)
        liquid = pd.read_csv(os.path.join(data_dir, "liquid_clean.csv"), index_col="Date", parse_dates=True)
    except FileNotFoundError as e:
        print(f"Clean data files not found: {e}. Please run preprocessing.py first.")
        return

    # Extract Close prices
    dfs = {"nifty": nifty, "gold": gold, "liquid": liquid}
    close_prices = pd.DataFrame({name: df['Close'] for name, df in dfs.items()})
    
    # Calculate indicators using pandas_ta for each column
    # EMA 20
    ema20 = close_prices.apply(lambda x: ta.ema(x, length=20))
    # SMA 50
    sma50 = close_prices.apply(lambda x: ta.sma(x, length=50))
    # RSI 14
    rsi14 = close_prices.apply(lambda x: ta.rsi(x, length=14))
    
    # ROC 63 (3-month) and ROC 126 (6-month)
    roc63 = close_prices.apply(lambda x: ta.roc(x, length=63))
    roc126 = close_prices.apply(lambda x: ta.roc(x, length=126))
    
    # MACD helper functions
    def get_macd_line(x):
        macd_df = ta.macd(x, fast=12, slow=26, signal=9)
        if macd_df is not None and not macd_df.empty:
            return macd_df.iloc[:, 0] # MACD line
        return pd.Series(index=x.index, dtype=float)
        
    def get_macd_signal(x):
        macd_df = ta.macd(x, fast=12, slow=26, signal=9)
        if macd_df is not None and not macd_df.empty:
            return macd_df.iloc[:, 2] # Signal line
        return pd.Series(index=x.index, dtype=float)

    macd_line = close_prices.apply(get_macd_line)
    macd_signal = close_prices.apply(get_macd_signal)
    
    # Save the features
    features_dir = os.path.join(data_dir, "features")
    os.makedirs(features_dir, exist_ok=True)
    
    close_prices.to_csv(os.path.join(features_dir, "close.csv"))
    ema20.to_csv(os.path.join(features_dir, "ema20.csv"))
    sma50.to_csv(os.path.join(features_dir, "sma50.csv"))
    rsi14.to_csv(os.path.join(features_dir, "rsi14.csv"))
    roc63.to_csv(os.path.join(features_dir, "roc63.csv"))
    roc126.to_csv(os.path.join(features_dir, "roc126.csv"))
    macd_line.to_csv(os.path.join(features_dir, "macd_line.csv"))
    macd_signal.to_csv(os.path.join(features_dir, "macd_signal.csv"))
    
    print("Feature generation complete.")

if __name__ == "__main__":
    generate_features()
