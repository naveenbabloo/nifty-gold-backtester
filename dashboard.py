import streamlit as st
import pandas as pd
import yaml
import os
import subprocess

st.set_page_config(page_title="Nifty/Gold Dual Momentum", layout="wide")

st.title("Nifty/Gold Dual Momentum Swing Backtester")

# Display config
try:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
        
    st.sidebar.header("Configuration")
    st.sidebar.json(config)
except FileNotFoundError:
    st.sidebar.error("Config not found")

# Run signal generator and display output
st.header("Daily Signal Generator")

if st.button("Generate Today's Signals"):
    with st.spinner("Fetching data and running logic..."):
        # Since the app might be run from the virtual environment or standard environment,
        # we try to use the current executable or fallback to python
        result = subprocess.run(["python", "generate_signals.py"], capture_output=True, text=True)
        if result.returncode == 0:
            st.code(result.stdout, language="text")
        else:
            st.error(f"Error running signal generator:\n{result.stderr}")
            
# Show data
st.header("Latest Pre-calculated Features")
try:
    features_dir = "data/features"
    if os.path.exists(features_dir):
        roc126 = pd.read_csv(os.path.join(features_dir, "roc126.csv"), index_col="Date")
        st.write("6-Month ROC (Latest 5 Days)")
        st.dataframe(roc126.tail())
        
        rsi14 = pd.read_csv(os.path.join(features_dir, "rsi14.csv"), index_col="Date")
        st.write("RSI 14 (Latest 5 Days)")
        st.dataframe(rsi14.tail())
    else:
        st.info("Features directory not found. Please run the data pipelines first.")
except Exception as e:
    st.warning(f"Could not load features: {e}")
