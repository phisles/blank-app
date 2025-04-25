import os
import requests
import streamlit as st
import pandas as pd
from datetime import datetime, date
from zoneinfo import ZoneInfo

API_KEY = st.secrets["APCA_API_KEY_ID"]
API_SECRET = st.secrets["APCA_API_SECRET_KEY"]
BASE_URL = st.secrets["APCA_API_BASE_URL"]

HEADERS = {
    "accept": "application/json",
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET
}

st.set_page_config(page_title="Alpaca Dashboard", layout="wide")
st.markdown("""
<style>
/* Force background and text to dark mode */
body, .main, .block-container {
    background-color: #0e1117 !important;
    color: #FFFFFF !important;
}

/* Force widget backgrounds and borders */
.stButton>button, .stSelectbox, .stTextInput>div>div>input,
.stDataFrame, .stMarkdown, .stTextArea>div>textarea {
    background-color: #1c1c1c !important;
    color: #FFFFFF !important;
    border: 1px solid #444 !important;
}

/* Dropdown & select box */
.css-1wa3eu0-control {
    background-color: #1c1c1c !important;
    color: #FFFFFF !important;
}

/* Table headers and cells */
thead tr th {
    background-color: #1c1c1c !important;
    color: #FFFFFF !important;
}
tbody tr td {
    background-color: #1c1c1c !important;
    color: #FFFFFF !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown("""<style>* { font-family: Courier, monospace !important; }</style>""", unsafe_allow_html=True)
st.title("📈 Alpaca Trading Algo: Live Portfolio Overview")

# --- Starting Values ---
STARTING_PORTFOLIO_VALUE = 2000.00
START_DATE = date(2025, 4, 22)
DAYS_RUNNING = (date.today() - START_DATE).days

# --- Fetch Functions ---
def fetch_portfolio_history(timeframe="5Min", period="1D"):
    url = (
        f"{BASE_URL}/v2/account/portfolio/history"
        f"?period={period}&timeframe={timeframe}&pnl_reset=continuous"
    )
    response = requests.get(url, headers=HEADERS)
    try:
        data = response.json()
    except Exception as e:
        st.error(f"❌ Failed to parse portfolio history: {e}")
        return pd.DataFrame()

    if "timestamp" not in data or not data["timestamp"]:
        st.warning("⚠️ No portfolio history data returned.")
        return pd.DataFrame()

    df = pd.DataFrame({
        "Time": [datetime.fromtimestamp(ts, tz=ZoneInfo("America/New_York")) for ts in data["timestamp"]],
        "P/L %": [v * 100 for v in data["profit_loss_pct"]],
        "P/L $": data["profit_loss"],
        "Equity": data["equity"]
    })
    return df

def fetch_account_info():
    response = requests.get(f"{BASE_URL}/v2/account", headers=HEADERS)
    return response.json()

def fetch_positions():
    response = requests.get(f"{BASE_URL}/v2/positions", headers=HEADERS)
    return response.json()

def fetch_account_activities():
    url = f"{BASE_URL}/v2/account/activities?direction=desc&page_size=100"
    response = requests.get(url, headers=HEADERS)
    return response.json()

# --- Account Summary ---
account_data = fetch_account_info()
latest_equity = float(account_data.get("portfolio_value", 0.0))
pl_dollar = latest_equity - STARTING_PORTFOLIO_VALUE
pl_percent = ((latest_equity - STARTING_PORTFOLIO_VALUE) / STARTING_PORTFOLIO_VALUE) * 100

# --- Widget-style Summary ---
# --- Widget-style Summary with Colors and Averages ---
# --- Summary Stats Setup ---
buying_power = float(account_data.get("buying_power", 0.0))
margin_used = float(account_data.get("initial_margin", 0.0))
margin_req = float(account_data.get("maintenance_margin", 0.0))

avg_pl_dollar = pl_dollar / DAYS_RUNNING if DAYS_RUNNING else 0
avg_pl_percent = pl_percent / DAYS_RUNNING if DAYS_RUNNING else 0

value_color = "green" if latest_equity > STARTING_PORTFOLIO_VALUE else "red"
pl_color = "green" if pl_dollar > 0 else "red" if pl_dollar < 0 else "black"
avg_color = "green" if avg_pl_dollar > 0 else "red" if avg_pl_dollar < 0 else "black"

# --- Wrapped Summary Boxes ---
st.markdown("""
<div style="padding: 10px 0 20px 0;">
""", unsafe_allow_html=True)

row1 = st.columns(2)
row1[0].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444; width: 100%;">
<div style="font-size:16px; color:#888;">Starting Value</div>
<div style="font-size:38px; font-family: Courier, monospace;">${STARTING_PORTFOLIO_VALUE:,.2f}</div>
</div>
""", unsafe_allow_html=True)

row1[1].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444; width: 100%;">
<div style="font-size:16px; color:#888;">Current Value</div>
<div style="font-size:38px; font-family: Courier, monospace; color:{value_color};">${latest_equity:,.2f}</div>
</div>
""", unsafe_allow_html=True)

row2 = st.columns(4)
row2[0].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444; width: 100%;">
<div style="font-size:15px; color:#888;">P/L $</div>
<div style="font-size:26px; font-family: Courier, monospace; color:{pl_color};">${pl_dollar:,.2f}</div>
</div>
""", unsafe_allow_html=True)

row2[1].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444; width: 100%;">
<div style="font-size:15px; color:#888;">P/L %</div>
<div style="font-size:26px; font-family: Courier, monospace; color:{pl_color};">{pl_percent:.2f}%</div>
</div>
""", unsafe_allow_html=True)

row2[2].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444; width: 100%;">
<div style="font-size:15px; color:#888;">Avg Daily $</div>
<div style="font-size:26px; font-family: Courier, monospace; color:{avg_color};">${avg_pl_dollar:.2f}</div>
</div>
""", unsafe_allow_html=True)

row2[3].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444; width: 100%;">
<div style="font-size:15px; color:#888;">Avg Daily %</div>
<div style="font-size:26px; font-family: Courier, monospace; color:{avg_color};">{avg_pl_percent:.2f}%</div>
</div>
""", unsafe_allow_html=True)

row3 = st.columns(3)
row3[0].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444; width: 100%;">
<div style="font-size:15px; color:#888;">Buying Power</div>
<div style="font-size:26px; font-family: Courier, monospace; color:#00ffcc;">${buying_power:,.2f}</div>
</div>
""", unsafe_allow_html=True)

row3[1].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444; width: 100%;">
<div style="font-size:15px; color:#888;">Margin Used</div>
<div style="font-size:26px; font-family: Courier, monospace; color:#ff6666;">${margin_used:,.2f}</div>
</div>
""", unsafe_allow_html=True)

row3[2].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444; width: 100%;">
<div style="font-size:15px; color:#888;">Margin Requirement</div>
<div style="font-size:26px; font-family: Courier, monospace; color:#ffaa00;">${margin_req:,.2f}</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="margin-top: 10px; margin-left:5px; margin-right:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444;">
<div style="font-size:15px; color:#888;">Started</div>
<div style="font-size:20px; font-family: Courier, monospace;">
{START_DATE.strftime('%B %d, %Y')} &nbsp; | &nbsp; Days Running: {DAYS_RUNNING}
</div>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

positions_data = fetch_positions()

if isinstance(positions_data, list) and positions_data:
    df = pd.DataFrame(positions_data)
    df = df.astype({
        "unrealized_pl": float,
        "unrealized_plpc": float,
        "unrealized_intraday_pl": float,
        "unrealized_intraday_plpc": float,
        "avg_entry_price": float,
        "current_price": float,
        "market_value": float,
        "cost_basis": float,
        "qty": float,
        "lastday_price": float,
        "change_today": float
    })
    df["unrealized_plpc"] *= 100
    df["unrealized_intraday_plpc"] *= 100
    df["change_today"] *= 100

    df_display = df[[
        "symbol", "qty", "side", "avg_entry_price", "current_price",
        "market_value", "cost_basis", "unrealized_pl", "unrealized_plpc",
        "unrealized_intraday_pl", "unrealized_intraday_plpc", "lastday_price", "change_today"
    ]].rename(columns={
        "symbol": "Symbol", "qty": "Qty", "side": "Side", "avg_entry_price": "Entry $",
        "current_price": "Cur $", "market_value": "Market Val", "cost_basis": "Cost Basis",
        "unrealized_pl": "PL $", "unrealized_plpc": "PL %", "unrealized_intraday_pl": "Intraday $",
        "unrealized_intraday_plpc": "Intraday %", "lastday_price": "LastDay $", "change_today": "Chg Today %"
    })

    def highlight_color(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return "color: green"
            elif val < 0:
                return "color: red"
        return ""
    df_display.reset_index(drop=True, inplace=True)
    st.dataframe(df_display.style.applymap(highlight_color, subset=[
        "PL $", "PL %", "Intraday $", "Intraday %", "Chg Today %"
    ]).format({
        "Entry $": "${:.2f}",
        "Cur $": "${:.2f}",
        "Market Val": "${:.2f}",
        "Cost Basis": "${:.2f}",
        "PL $": "${:.2f}",
        "PL %": "{:.2f}%",
        "Intraday $": "${:.2f}",
        "Intraday %": "{:.2f}%",
        "LastDay $": "${:.2f}",
        "Chg Today %": "{:.2f}%"
    }), use_container_width=True)
else:
    st.warning("No positions found.")

# --- Activities ---
st.subheader("📜 Recent Account Activities")
activities_data = fetch_account_activities()

if isinstance(activities_data, list) and activities_data:
    df_activities = pd.DataFrame(activities_data)
    df_activities["transaction_time"] = pd.to_datetime(df_activities["transaction_time"])
    df_activities["Price"] = pd.to_numeric(df_activities["price"], errors="coerce")
    df_activities["Qty"] = pd.to_numeric(df_activities["qty"], errors="coerce")

    df_display = df_activities[[
        "activity_type", "symbol", "Qty", "Price", "side", "transaction_time"
    ]].rename(columns={
        "activity_type": "Type", "symbol": "Symbol", "side": "Side", "transaction_time": "Time"
    })

    col1, col2, col3, col4 = st.columns(4)
    activity_types = ["All"] + sorted(df_display["Type"].dropna().unique())
    symbols = ["All"] + sorted(df_display["Symbol"].dropna().unique())
    sides = ["All"] + sorted(df_display["Side"].dropna().unique())
    dates = ["All"] + sorted(df_display["Time"].dt.date.unique().astype(str))
    
    with col1:
        filter_type = st.selectbox("Activity Type", options=activity_types)
    with col2:
        filter_symbol = st.selectbox("Symbol", options=symbols)
    with col3:
        filter_side = st.selectbox("Side", options=sides)
    with col4:
        filter_date = st.selectbox("Date", options=dates)
    
    if filter_type != "All":
        df_display = df_display[df_display["Type"] == filter_type]
    if filter_symbol != "All":
        df_display = df_display[df_display["Symbol"] == filter_symbol]
    if filter_side != "All":
        df_display = df_display[df_display["Side"] == filter_side]
    if filter_date != "All":
        df_display = df_display[df_display["Time"].dt.date.astype(str) == filter_date]

    df_display = df_display.sort_values("Time", ascending=False)

    def highlight_activities(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return "color: green"
            elif val < 0:
                return "color: red"
        return ""
    df_display.reset_index(drop=True, inplace=True)
    st.dataframe(df_display.style.applymap(highlight_activities, subset=["Qty", "Price"]).format({
        "Price": "${:.2f}",
        "Qty": "{:.2f}"
    }), use_container_width=True)
else:
    st.warning("No recent account activity found.")
