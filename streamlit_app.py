import os
import requests
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from zoneinfo import ZoneInfo

# Load from Streamlit secrets
API_KEY = st.secrets["APCA_API_KEY_ID"]
API_SECRET = st.secrets["APCA_API_SECRET_KEY"]
BASE_URL = st.secrets["APCA_API_BASE_URL"]

HEADERS = {
    "accept": "application/json",
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET
}

st.set_page_config(page_title="📈 Alpaca Portfolio Dashboard", layout="wide")
st.title("📊 Alpaca Trading Algo: Live Portfolio Overview")

# --- Functions ---
def fetch_portfolio_history(timeframe, period):
    url = (
        f"{BASE_URL}/v2/account/portfolio/history"
        f"?period={period}&timeframe={timeframe}&intraday_reporting=extended_hours"
        + ("&pnl_reset=per_day" if timeframe != "1D" else "")
    )
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    if "timestamp" not in data:
        st.error(f"Alpaca Error: {data}")
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

# --- Portfolio History Charts ---
st.subheader("📊 Portfolio Equity Over Time")
hourly_df = fetch_portfolio_history("1H", "1D")
daily_df = fetch_portfolio_history("1D", "1W")

if not hourly_df.empty:
    st.altair_chart(
        alt.Chart(hourly_df).mark_line(point=True).encode(
            x="Time:T",
            y=alt.Y("Equity:Q", title="Equity ($)"),
            tooltip=["Time:T", "Equity:Q"]
        ).properties(title="Equity (Hourly View)", width="container"), use_container_width=True
    )

if not daily_df.empty:
    st.altair_chart(
        alt.Chart(daily_df).mark_line(point=True).encode(
            x="Time:T",
            y=alt.Y("Equity:Q", title="Equity ($)"),
            tooltip=["Time:T", "Equity:Q"]
        ).properties(title="Equity (Daily View)", width="container"), use_container_width=True
    )

st.subheader("📈 Profit / Loss Percent Over Time")
if not daily_df.empty:
    st.altair_chart(
        alt.Chart(daily_df).mark_bar().encode(
            x="Time:T",
            y=alt.Y("P/L %:Q", title="P/L %"),
            color=alt.condition("datum['P/L %'] >= 0", alt.value("green"), alt.value("red")),
            tooltip=["Time:T", "P/L %:Q"]
        ).properties(title="P/L % by Day", width="container"), use_container_width=True
    )

# --- Account Summary ---
st.subheader("📋 Account Summary")
account_data = fetch_account_info()
st.markdown(f"""
- 💰 **Equity**: ${float(account_data.get("equity", 0.0)):,}
- 🧾 **Portfolio Value**: ${float(account_data.get("portfolio_value", 0.0)):,}
- 💵 **Buying Power**: ${float(account_data.get("buying_power", 0.0)):,}
- 📉 **Margin Used**: ${float(account_data.get("margin_used", 0.0)):,}
- 📊 **Maintenance Margin**: ${float(account_data.get("maintenance_margin", 0.0)):,}
""")

# --- Current Positions ---
st.subheader("📈 Current Positions")
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

    st.dataframe(df_display.style.format({
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

# --- Account Activities ---
st.subheader("📜 Recent Account Activities")
activities_data = fetch_account_activities()

if isinstance(activities_data, list) and activities_data:
    df_activities = pd.DataFrame(activities_data)
    df_activities["transaction_time"] = pd.to_datetime(df_activities["transaction_time"])
    df_display = df_activities[[
        "activity_type", "symbol", "qty", "price", "side", "transaction_time", "id"
    ]].rename(columns={
        "activity_type": "Type", "symbol": "Symbol", "qty": "Qty",
        "price": "Price", "side": "Side", "transaction_time": "Time", "id": "ID"
    })

    st.dataframe(df_display.sort_values("Time", ascending=False).style.format({
        "Price": "${:.2f}",
        "Qty": "{:.2f}"
    }), use_container_width=True)
else:
    st.warning("No recent account activity found.")
