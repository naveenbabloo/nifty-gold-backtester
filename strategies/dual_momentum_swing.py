import numpy as np
import pandas as pd
import os

def load_data(data_dir="data"):
    # Load prices
    nifty = pd.read_csv(os.path.join(data_dir, "nifty_clean.csv"), index_col="Date", parse_dates=True)
    gold = pd.read_csv(os.path.join(data_dir, "gold_clean.csv"), index_col="Date", parse_dates=True)
    liquid = pd.read_csv(os.path.join(data_dir, "liquid_clean.csv"), index_col="Date", parse_dates=True)
    
    high = pd.DataFrame({"nifty": nifty['High'], "gold": gold['High'], "liquid": liquid['High']})
    low = pd.DataFrame({"nifty": nifty['Low'], "gold": gold['Low'], "liquid": liquid['Low']})
    
    features_dir = os.path.join(data_dir, "features")
    def load_feature(name):
        return pd.read_csv(os.path.join(features_dir, f"{name}.csv"), index_col="Date", parse_dates=True)
        
    return {
        "high": high,
        "low": low,
        "close": load_feature("close"),
        "ema20": load_feature("ema20"),
        "sma50": load_feature("sma50"),
        "rsi14": load_feature("rsi14"),
        "roc126": load_feature("roc126"),
        "macd_line": load_feature("macd_line"),
        "macd_signal": load_feature("macd_signal")
    }

def generate_signals(data):
    high = data["high"]
    low = data["low"]
    close = data["close"]
    ema20 = data["ema20"]
    sma50 = data["sma50"]
    rsi14 = data["rsi14"]
    roc126 = data["roc126"]
    macd_line = data["macd_line"]
    macd_signal = data["macd_signal"]
    
    assets = ["nifty", "gold", "liquid"]
    
    # 1. Macro Regime Filter (Dual Momentum)
    max_roc_asset = roc126.idxmax(axis=1)
    
    active_asset = pd.DataFrame(index=roc126.index, columns=assets, data=False)
    for asset in assets:
        active_asset[asset] = (max_roc_asset == asset)
        
    # 2. Swing Execution Layer
    pullback = (low <= ema20) & (high >= ema20)
    proximity = (close <= ema20 * 1.015) & (close >= ema20 * 0.985)
    pullback_condition = pullback | proximity
    
    rsi_condition = (rsi14 > 40) & (rsi14 < 70)
    
    entries = pd.DataFrame(index=close.index, columns=assets, data=False)
    
    for asset in ["nifty", "gold"]:
        entries[asset] = active_asset[asset] & pullback_condition[asset] & rsi_condition[asset]
        
    entries["liquid"] = active_asset["liquid"] & (~active_asset["liquid"].shift(1).fillna(False)) # Entry only on transition
    
    # 3. Exit & Risk Mitigation Logic
    macd_cross_below = (macd_line < macd_signal) & (macd_line.shift(1) >= macd_signal.shift(1))
    close_below_sma = close < sma50
    regime_shift = ~active_asset
    
    exits = pd.DataFrame(index=close.index, columns=assets, data=False)
    for asset in ["nifty", "gold"]:
        exits[asset] = macd_cross_below[asset] | close_below_sma[asset] | regime_shift[asset]
        
    exits["liquid"] = regime_shift["liquid"]
    
    return entries, exits, active_asset

if __name__ == "__main__":
    data = load_data()
    entries, exits, active_asset = generate_signals(data)
    print("Entries:")
    print(entries.sum())
    print("\nExits:")
    print(exits.sum())
