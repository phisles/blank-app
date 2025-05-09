import os
import requests
import streamlit as st
import pandas as pd
from datetime import datetime, date
from zoneinfo import ZoneInfo
import json
import time  # Add time import to use sleep
import numpy as np
import altair as alt  # ✅ Make sure this is imported at the top

API_KEY = st.secrets["APCA_API_KEY_ID"]
API_SECRET = st.secrets["APCA_API_SECRET_KEY"]
BASE_URL = st.secrets["APCA_API_BASE_URL"]

HEADERS = {
    "accept": "application/json",
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET
}

st.set_page_config(page_title="AI Hedge Fund Dashboard", layout="wide")
st.markdown("""<style>* { font-family: Courier, monospace !important; }</style>""", unsafe_allow_html=True)
st.title("AI Hedge Fund Simulator")

# --- Starting Values ---
STARTING_PORTFOLIO_VALUE = 2000.00
START_DATE = date(2025, 4, 28)
DAYS_RUNNING = (date.today() - START_DATE).days

st.markdown(f"""
<div style="margin-top: 10px; margin-left:5px; margin-right:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444;">
<div style="font-size:15px; color:#888;">Started</div>
<div style="font-size:20px; font-family: Courier, monospace; color:#ffffff;">
{START_DATE.strftime('%B %d, %Y')} &nbsp; | &nbsp; Days Running: {DAYS_RUNNING}
</div>
</div>
""", unsafe_allow_html=True)

# --- Fetch Functions ---
def fetch_portfolio_history(timeframe="1D", period="5D"):
    url = (
        f"{BASE_URL}/v2/account/portfolio/history"
        f"?period={period}&timeframe={timeframe}&pnl_reset=continuous"
    )
    response = requests.get(url, headers=HEADERS)
    try:
        data = response.json()
        #st.code(json.dumps(data, indent=2))  # 🔍 Print raw JSON in the app
    except Exception as e:
        st.error(f"❌ Failed to parse portfolio history: {e}")
        st.code(response.text)  # Show raw text if JSON parsing fails
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
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444;">
<div style="font-size:16px; color:#888;">Starting Value</div>
<div style="font-size:38px; font-family: Courier, monospace; color:#ffffff;">${STARTING_PORTFOLIO_VALUE:,.2f}</div>
</div>
""", unsafe_allow_html=True)

row1[1].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444;">
<div style="font-size:16px; color:#888;">Current Value</div>
<div style="font-size:38px; font-family: Courier, monospace; color:{value_color};">${latest_equity:,.2f}</div>
</div>
""", unsafe_allow_html=True)

row2 = st.columns(4)
row2[0].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444;">
<div style="font-size:15px; color:#888;">P/L $</div>
<div style="font-size:26px; font-family: Courier, monospace; color:{pl_color};">${pl_dollar:,.2f}</div>
</div>
""", unsafe_allow_html=True)

row2[1].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444;">
<div style="font-size:15px; color:#888;">P/L %</div>
<div style="font-size:26px; font-family: Courier, monospace; color:{pl_color};">{pl_percent:.2f}%</div>
</div>
""", unsafe_allow_html=True)

row2[2].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444;">
<div style="font-size:15px; color:#888;">Avg Daily $</div>
<div style="font-size:26px; font-family: Courier, monospace; color:{avg_color};">${avg_pl_dollar:.2f}</div>
</div>
""", unsafe_allow_html=True)

row2[3].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444;">
<div style="font-size:15px; color:#888;">Avg Daily %</div>
<div style="font-size:26px; font-family: Courier, monospace; color:{avg_color};">{avg_pl_percent:.2f}%</div>
</div>
""", unsafe_allow_html=True)

row3 = st.columns(3)
row3[0].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444;">
<div style="font-size:15px; color:#888;">Buying Power</div>
<div style="font-size:26px; font-family: Courier, monospace; color:#00ffcc;">${buying_power:,.2f}</div>
</div>
""", unsafe_allow_html=True)


# --- Filtered Daily History Table ---
history_df = fetch_portfolio_history(timeframe="1D", period="1M")
cleaned_history = history_df[
    ~((history_df["P/L %"] == 0) & (history_df["P/L $"] == 0) & (history_df["Equity"] == 0))
].copy()

if not cleaned_history.empty:
    st.markdown("""
    <div style="margin:15px 0 5px 0; font-size:18px; font-weight:bold; color:#00ffcc;">
        📅 Portfolio P&L History (1D Resolution)
    </div>
    """, unsafe_allow_html=True)

    row5 = st.columns(1)
    with row5[0]:

        # Clean values
        chart_data = cleaned_history.copy()
        chart_data["Equity"] = chart_data["Equity"].replace('[\$,]', '', regex=True).astype(float)
        chart_data["P/L $"] = chart_data["P/L $"].replace('[\$,]', '', regex=True).astype(float)
        chart_data["P/L %"] = chart_data["P/L %"].replace('%', '', regex=True).astype(float)

        # Selectbox to toggle metric
        selected_metric = st.selectbox("Select Metric", ["Equity", "P/L $", "P/L %"])

        y_min = chart_data[selected_metric].min()
        y_max = chart_data[selected_metric].max()
        y_range = y_max - y_min
        padding = y_range * 0.1 if y_range > 0 else 10

        line = alt.Chart(chart_data).mark_line(color="#00ffcc").encode(
            x=alt.X("Time:T", title="Date"),
            y=alt.Y(f"{selected_metric}:Q", title=selected_metric,
                    scale=alt.Scale(domain=[y_min - padding, y_max + padding])),
            tooltip=[
                alt.Tooltip("Time:T", title="Date"),
                alt.Tooltip("Equity:Q", format="$.2f", title="Equity"),
                alt.Tooltip("P/L $:Q", format="$.2f", title="P/L $"),
                alt.Tooltip("P/L %:Q", format=".2f", title="P/L %")
            ]
        ).properties(
            height=300
        )

        st.altair_chart(line.interactive(), use_container_width=True)
else:
    st.info("No meaningful portfolio history data to display.")

row4 = st.columns(1)
if not history_df.empty:
    returns = history_df["P/L %"]
    returns = returns[returns != 0]  # Filter out zero-change days
    
    if not returns.empty:
        average_daily_return = returns.mean()
        std_dev_return = returns.std()
        sharpe_ratio = average_daily_return / std_dev_return if std_dev_return != 0 else 0
    else:
        sharpe_ratio = 0
    sharpe_ratio = average_daily_return / std_dev_return if std_dev_return != 0 else 0
    sharpe_color = "#00ffcc" if sharpe_ratio > 1 else "#ffaa00" if sharpe_ratio > 0.5 else "#ff6666"

    row4[0].markdown(f"""
    <div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444;">
    <div style="font-size:15px; color:#888;">Sharpe Ratio (1M)</div>
    <div style="font-size:26px; font-family: Courier, monospace; color:{sharpe_color};">{sharpe_ratio:.2f}</div>
    </div>
    """, unsafe_allow_html=True)
else:
    row4[0].warning("⚠️ No portfolio history available for Sharpe Ratio.")

row3[1].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444;">
<div style="font-size:15px; color:#888;">Margin Used</div>
<div style="font-size:26px; font-family: Courier, monospace; color:#ff6666;">${margin_used:,.2f}</div>
</div>
""", unsafe_allow_html=True)

row3[2].markdown(f"""
<div style="margin:5px; padding:12px; border-radius:8px; background-color:#2a2a2a; border:1px solid #444;">
<div style="font-size:15px; color:#888;">Margin Requirement</div>
<div style="font-size:26px; font-family: Courier, monospace; color:#ffaa00;">${margin_req:,.2f}</div>
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
st.subheader("Recent Account Activities")
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

st.markdown("""
<iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_abcde&symbol=NASDAQ%3AAAPL&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=dark&style=1&timezone=Etc%2FUTC&withdateranges=1&hidevolume=1&hideideas=1&watchlist=NASDAQ%3AAAPL%2CNASDAQ%3AMSFT%2CNASDAQ%3ATSLA%2CNASDAQ%3AAMZN%2CNASDAQ%3AGOOG&utm_source=yourdomain.com&utm_medium=widget&utm_campaign=chart&utm_term=NASDAQ%3AAAPL" 
width="100%" height="400" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
""", unsafe_allow_html=True)

st.markdown("""
<iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_abcde&symbol=NASDAQ%3AMSFT&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=dark&style=1&timezone=Etc%2FUTC&withdateranges=1&hidevolume=1&hideideas=1&watchlist=NASDAQ%3AAAPL%2CNASDAQ%3AMSFT%2CNASDAQ%3ATSLA%2CNASDAQ%3AAMZN%2CNASDAQ%3AGOOG&utm_source=yourdomain.com&utm_medium=widget&utm_campaign=chart&utm_term=NASDAQ%3AAAPL" 
width="100%" height="400" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
""", unsafe_allow_html=True)

st.markdown("""
<iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_abcde&symbol=NASDAQ%3AGOOGL&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=dark&style=1&timezone=Etc%2FUTC&withdateranges=1&hidevolume=1&hideideas=1&watchlist=NASDAQ%3AAAPL%2CNASDAQ%3AMSFT%2CNASDAQ%3ATSLA%2CNASDAQ%3AAMZN%2CNASDAQ%3AGOOG&utm_source=yourdomain.com&utm_medium=widget&utm_campaign=chart&utm_term=NASDAQ%3AAAPL" 
width="100%" height="400" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
""", unsafe_allow_html=True)

st.markdown("""
<iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_abcde&symbol=NASDAQ%3ATSLA&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=dark&style=1&timezone=Etc%2FUTC&withdateranges=1&hidevolume=1&hideideas=1&watchlist=NASDAQ%3AAAPL%2CNASDAQ%3AMSFT%2CNASDAQ%3ATSLA%2CNASDAQ%3AAMZN%2CNASDAQ%3AGOOG&utm_source=yourdomain.com&utm_medium=widget&utm_campaign=chart&utm_term=NASDAQ%3AAAPL" 
width="100%" height="400" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
""", unsafe_allow_html=True)

st.markdown("""
<iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_abcde&symbol=NASDAQ%3ANVDA&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=dark&style=1&timezone=Etc%2FUTC&withdateranges=1&hidevolume=1&hideideas=1&watchlist=NASDAQ%3AAAPL%2CNASDAQ%3AMSFT%2CNASDAQ%3ATSLA%2CNASDAQ%3AAMZN%2CNASDAQ%3AGOOG&utm_source=yourdomain.com&utm_medium=widget&utm_campaign=chart&utm_term=NASDAQ%3AAAPL" 
width="100%" height="400" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
""", unsafe_allow_html=True)
