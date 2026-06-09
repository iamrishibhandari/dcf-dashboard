import streamlit as st
import yfinance as yf

st.title("DCF Valuation Dashboard")

ticker = st.text_input("Enter Stock Ticker (e.g. AAPL)", value="AAPL")

if ticker:
    stock = yf.Ticker(ticker)
    import time
time.sleep(2)
info = stock.info

    st.subheader(f"{info.get('longName', ticker)}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"${info.get('currentPrice', 'N/A')}")
    col2.metric("Revenue", f"${info.get('totalRevenue', 0):,}")
    col3.metric("Net Income", f"${info.get('netIncomeToCommon', 0):,}")

    st.subheader("DCF Assumptions")
    growth_rate = st.slider("Revenue Growth Rate (%)", 0, 30, 10) / 100
    discount_rate = st.slider("Discount Rate / WACC (%)", 5, 20, 10) / 100
    terminal_growth = st.slider("Terminal Growth Rate (%)", 0, 5, 2) / 100
    years = st.slider("Projection Years", 3, 10, 5)

    fcf = info.get('freeCashflow', 0)

    if fcf and fcf > 0:
        projected_fcf = []
        for i in range(1, years + 1):
            projected_fcf.append(fcf * (1 + growth_rate) ** i)

        pv_fcf = sum([cf / (1 + discount_rate) ** i for i, cf in enumerate(projected_fcf, 1)])
        terminal_value = projected_fcf[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / (1 + discount_rate) ** years
        enterprise_value = pv_fcf + pv_terminal
        shares = info.get('sharesOutstanding', 1)
        intrinsic_value = enterprise_value / shares

        st.subheader("DCF Output")
        col4, col5, col6 = st.columns(3)
        col4.metric("PV of FCFs", f"${pv_fcf:,.0f}")
        col5.metric("PV of Terminal Value", f"${pv_terminal:,.0f}")
        col6.metric("Intrinsic Value Per Share", f"${intrinsic_value:.2f}")

        current_price = info.get('currentPrice', 0)
        if current_price:
            upside = ((intrinsic_value - current_price) / current_price) * 100
            st.metric("Upside / Downside vs Current Price", f"{upside:.1f}%")
    else:
        st.warning("No free cash flow data available for this ticker.")
