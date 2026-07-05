import streamlit as st
import pandas as pd
import yaml
import plotly.graph_objects as go
from generate_signals import run_daily_logic

st.set_page_config(page_title="Nifty/Gold Dual Momentum", layout="wide", initial_sidebar_state="expanded")

# Apply modern dark theme CSS
st.markdown("""
<style>
    .reportview-container {
        background: #0E1117;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #FF4B2B, #FF416C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .action-card {
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .action-card.green { background: linear-gradient(135deg, #11998e, #38ef7d); }
    .action-card.red { background: linear-gradient(135deg, #cb2d3e, #ef473a); }
    .action-card.yellow { background: linear-gradient(135deg, #f7971e, #ffd200); color: black; }
    .action-card.blue { background: linear-gradient(135deg, #2193b0, #6dd5ed); }
    .action-card.gray { background: linear-gradient(135deg, #4b6cb7, #182848); }
    .action-card h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    .action-card p { margin: 5px 0 0 0; font-size: 1.1rem; opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

def check_password():
    def password_entered():
        if st.session_state["password"] == "backtest2026": 
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Please enter the password to access the dashboard", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Please enter the password to access the dashboard", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- Config Sidebar ---
with st.sidebar:
    st.title("⚙️ Parameters")
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        st.markdown("**Capital & Fees**")
        st.write(f"Initial Capital: ₹{config.get('capital', 100000):,}")
        st.write(f"Brokerage (Per Trade): ₹{config.get('fees', 20)}")
        st.write(f"Slippage: {config.get('slippage', 0) * 100}%")
        
        st.markdown("**Tax Regime (2026)**")
        tax = config.get("tax_rates", {})
        st.write(f"STCG (Equity): {tax.get('equity_stcg', 0) * 100}%")
        st.write(f"LTCG (Equity): {tax.get('equity_ltcg', 0) * 100}%")
        
    except Exception as e:
        st.error(f"Config error: {e}")

st.markdown('<p class="main-header">Nifty/Gold Dual Momentum Engine</p>', unsafe_allow_html=True)
st.markdown("Automated quantitative regime-switching system. Generates actionable signals based on 6M Relative Strength and EMA pullbacks.")
st.markdown("---")

if st.button("🚀 Analyze Today's Market", use_container_width=True):
    with st.spinner("Fetching latest market data & calculating indicators..."):
        results = run_daily_logic()
        
    if "error" in results:
        st.error(results["error"])
        st.stop()
        
    date_str = results['date']
    st.subheader(f"📅 Market State for {date_str}")
    
    # 1. Top Action Cards
    st.markdown("### Executive Action Plan")
    col1, col2, col3 = st.columns(3)
    
    mapping = {"nifty": col1, "gold": col2, "liquid": col3}
    for asset, data in results["signals"].items():
        color_class = data["color"]
        action = data["action"]
        reason = data["reason"]
        
        with mapping[asset]:
            st.markdown(f"""
            <div class="action-card {color_class}">
                <h2>{action} {asset.upper()}</h2>
                <p>{reason}</p>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("---")
    
    # 2. Market Regime & Momentum
    st.markdown("### Macro Regime (6-Month Momentum)")
    m_col1, m_col2, m_col3 = st.columns(3)
    
    m_col1.metric("NIFTY 6M ROC", f"{results['roc']['nifty']:.2f}%", 
                  f"{results['roc']['nifty'] - results['roc']['gold']:.2f}% vs Gold")
    m_col2.metric("GOLD 6M ROC", f"{results['roc']['gold']:.2f}%",
                  f"{results['roc']['gold'] - results['roc']['nifty']:.2f}% vs Nifty")
    m_col3.metric("LIQUID 6M ROC", f"{results['roc']['liquid']:.2f}%")
    
    active_asset = results['active_asset']
    st.info(f"💡 **Current Regime:** Capital should be allocated to **{active_asset.upper()}** because it has the highest 6-month momentum.")

    st.markdown("---")

    # 3. Interactive Chart
    if active_asset in results["chart_data"]:
        st.markdown(f"### Tactical Entry Setup: {active_asset.upper()}")
        
        df = pd.DataFrame(results["chart_data"][active_asset])
        df['Date'] = pd.to_datetime(df['Date'])
        
        fig = go.Figure()
        
        # Candlesticks
        fig.add_trace(go.Candlestick(
            x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name="Price",
            increasing_line_color='#00ff88', decreasing_line_color='#ff0066'
        ))
        
        # EMA20
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['EMA20'], 
            line=dict(color='#00d4ff', width=2),
            name="20 EMA (Pullback Target)"
        ))
        
        # SMA50
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['SMA50'], 
            line=dict(color='#ff9900', width=2, dash='dot'),
            name="50 SMA (Trend Support)"
        ))
        
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0),
            height=500,
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tactical Metrics
        metrics = results["signals"][active_asset]["metrics"]
        t_col1, t_col2, t_col3, t_col4 = st.columns(4)
        t_col1.metric("Current Price", f"₹{metrics['close']:.2f}")
        t_col2.metric("20 EMA", f"₹{metrics['ema20']:.2f}")
        t_col3.metric("Distance to 20 EMA", f"{(metrics['close']/metrics['ema20'] - 1)*100:.2f}%")
        t_col4.metric("RSI (14)", f"{metrics['rsi14']:.2f}")
