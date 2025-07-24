import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Streamlit page config
st.set_page_config(page_title="AI ETF SIP Tracker", page_icon="🤖", layout="centered")

st.title("🤖 AI ETF SIP & Lumpsum Tracker")

# ETF data dictionary
etfs = {
    "Global X Robotics & AI (BOTZ)": {
        "ticker": "BOTZ",
        "expense_ratio": "0.69%",
        "focus": "Robotics + AI hardware"
    },
    "ARK Autonomous Tech & Robotics (ARKQ)": {
        "ticker": "ARKQ",
        "expense_ratio": "0.75%",
        "focus": "Disruptive AI + Automation"
    },
    "iShares AI ETF (IRBO)": {
        "ticker": "IRBO",
        "expense_ratio": "0.47%",
        "focus": "Broad AI + Small Caps"
    }
}

# User inputs
selected_etf = st.selectbox("Choose an AI ETF", list(etfs.keys()))
ticker = etfs[selected_etf]["ticker"]
investment_mode = st.radio("Investment Mode", ["SIP", "Lumpsum"])
amount = st.number_input(
    "Investment Amount ($ per month for SIP / one-time for Lumpsum)",
    min_value=50,
    value=500
)
months = st.slider("Investment Duration (in months)", min_value=6, max_value=60, value=12)

# Display ETF info
st.markdown(f"**Expense Ratio:** {etfs[selected_etf]['expense_ratio']} | **Focus Area:** {etfs[selected_etf]['focus']}")

# Fetch data with caching
@st.cache_data
def fetch_data(ticker, months):
    end = datetime.today()
    start = end - timedelta(days=months * 30)
    data = yf.download(ticker, start=start, end=end)
    return data

data = fetch_data(ticker, months)

if data.empty:
    st.error("No data available. Try a different ETF or reduce time period.")
else:
    # Prepare data
    data = data["Close"]
    data = data.resample("M").last().dropna()

    if investment_mode == "SIP":
        units = []
        invested = []
        values = []

        for i in range(len(data)):
            price = data.iloc[i]
            unit = amount / price
            units.append(unit)
            invested.append(amount * (i + 1))
            values.append(sum(units) * price)

        df_plot = pd.DataFrame({
            "Month": data.index.strftime("%b %Y"),
            "Invested Amount": invested,
            "Market Value": values
        })

    else:  # Lumpsum
        invested_amount = amount
        units = amount / data.iloc[0]
        values = [units * price for price in data]
        invested = [amount] * len(data)
        df_plot = pd.DataFrame({
            "Month": data.index.strftime("%b %Y"),
            "Invested Amount": invested,
            "Market Value": values
        })

    # Plot with Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_plot["Month"], y=df_plot["Invested Amount"],
        mode='lines+markers', name='Invested Amount'
    ))
    fig.add_trace(go.Scatter(
        x=df_plot["Month"], y=df_plot["Market Value"],
        mode='lines+markers', name='Market Value'
    ))

    fig.update_layout(
        title=f"{selected_etf} - {investment_mode} Growth",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        hovermode="x unified"
    )

    st.plotly_chart(fig)

    # Summary with corrected float conversion
    final_invested = float(invested[-1])
    final_value = float(values[-1])

    st.subheader("📊 Summary")
    st.write(f"**Total Invested:** ${final_invested:,.2f}")
    st.write(f"**Current Value:** ${final_value:,.2f}")
    st.write(f"**Return:** {((final_value - final_invested) / final_invested) * 100:.2f}%")

    # Download button
    csv = df_plot.to_csv(index=False)
    st.download_button("📥 Download SIP Data", csv, "ai_etf_sip.csv", "text/csv")
