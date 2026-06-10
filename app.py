import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="DCF Valuation Dashboard", layout="wide")
st.title("📈 DCF Valuation Dashboard")
st.caption("Built by Rishi Bhandari | Live data via yfinance")

ticker = st.text_input("Enter Stock Ticker (e.g. AAPL)", value="AAPL").upper()

if ticker:
    with st.spinner(f"Fetching data for {ticker}..."):
        stock = yf.Ticker(ticker)
        time.sleep(2)
        info = stock.info

    st.subheader(f"{info.get('longName', ticker)}")
    st.caption(f"{info.get('sector', '')} | {info.get('industry', '')}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"${info.get('currentPrice', 'N/A'):,}")
    col2.metric("Revenue", f"${info.get('totalRevenue', 0) / 1e9:.2f}B")
    col3.metric("Net Income", f"${info.get('netIncomeToCommon', 0) / 1e9:.2f}B")

    st.divider()
    st.subheader("DCF Assumptions")

    col_a, col_b = st.columns(2)
    with col_a:
        growth_rate = st.slider("Revenue Growth Rate (%)", 0, 30, 10) / 100
        discount_rate = st.slider("Discount Rate / WACC (%)", 5, 20, 10) / 100
    with col_b:
        terminal_growth = st.slider("Terminal Growth Rate (%)", 0, 5, 2) / 100
        years = st.slider("Projection Years", 3, 10, 5)

    fcf = info.get('freeCashflow', 0)

    if fcf and fcf > 0:
        projected_fcf = []
        pv_fcfs = []
        for i in range(1, years + 1):
            cf = fcf * (1 + growth_rate) ** i
            pv = cf / (1 + discount_rate) ** i
            projected_fcf.append(cf)
            pv_fcfs.append(pv)

        pv_fcf = sum(pv_fcfs)
        terminal_value = projected_fcf[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / (1 + discount_rate) ** years
        enterprise_value = pv_fcf + pv_terminal
        shares = info.get('sharesOutstanding', 1)
        intrinsic_value = enterprise_value / shares

        st.divider()
        st.subheader("Projected Free Cash Flows")

        chart_data = pd.DataFrame({
            "Year": [f"Year {i}" for i in range(1, years + 1)],
            "Projected FCF ($B)": [cf / 1e9 for cf in projected_fcf],
            "PV of FCF ($B)": [pv / 1e9 for pv in pv_fcfs]
        }).set_index("Year")
        st.bar_chart(chart_data)

        st.divider()
        st.subheader("DCF Output")
        col4, col5, col6 = st.columns(3)
        col4.metric("PV of FCFs", f"${pv_fcf / 1e9:.2f}B")
        col5.metric("PV of Terminal Value", f"${pv_terminal / 1e9:.2f}B")
        col6.metric("Intrinsic Value Per Share", f"${intrinsic_value:.2f}")

        current_price = info.get('currentPrice', 0)
        if current_price:
            upside = ((intrinsic_value - current_price) / current_price) * 100
            if upside > 0:
                st.success(f"📈 Upside vs Current Price: +{upside:.1f}%")
            else:
                st.error(f"📉 Downside vs Current Price: {upside:.1f}%")

        st.divider()
        st.subheader("Valuation Summary")
        summary = pd.DataFrame({
            "Metric": ["Current Price", "Intrinsic Value (DCF)", "Enterprise Value", "Upside / Downside"],
            "Value": [
                f"${current_price:.2f}",
                f"${intrinsic_value:.2f}",
                f"${enterprise_value / 1e9:.2f}B",
                f"{upside:.1f}%"
            ]
        })
        st.table(summary)

    else:
        st.warning("No free cash flow data available for this ticker.")