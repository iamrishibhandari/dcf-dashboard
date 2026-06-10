import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="DCF Valuation Dashboard", layout="wide", page_icon="💹")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .main-header { 
        background: linear-gradient(135deg, #1a1f2e, #16213e);
        padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem;
        border: 1px solid #2d3748;
    }
    .metric-card {
        background: #1a1f2e; border-radius: 10px;
        padding: 1rem; border: 1px solid #2d3748;
    }
    .stMetric { background: #1a1f2e; border-radius: 10px; padding: 1rem; border: 1px solid #2d3748; }
    div[data-testid="stMetricValue"] { color: #63b3ed; font-size: 1.8rem; }
    div[data-testid="stMetricLabel"] { color: #a0aec0; }
    .stSlider > div > div { background: #2d3748; }
    h1, h2, h3 { color: #e2e8f0 !important; }
    .stCaption { color: #718096 !important; }
    .stTable { background: #1a1f2e; }
    thead tr th { background: #2d3748 !important; color: #63b3ed !important; }
    tbody tr td { color: #e2e8f0 !important; }
    tbody tr:nth-child(even) { background: #1a1f2e !important; }
    tbody tr:nth-child(odd) { background: #16213e !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("DCF Valuation Dashboard")
st.caption("Built by Rishi Bhandari | Live market data via yfinance")
st.markdown('</div>', unsafe_allow_html=True)

ticker = st.text_input("Enter Stock Ticker", value="AAPL", placeholder="e.g. AAPL, TSLA, MSFT").upper()

def format_value(val):
    if abs(val) >= 1e12:
        return f"${val/1e12:.2f}T"
    elif abs(val) >= 1e9:
        return f"${val/1e9:.2f}B"
    elif abs(val) >= 1e6:
        return f"${val/1e6:.2f}M"
    else:
        return f"${val:,.0f}"

if ticker:
    with st.spinner(f"Fetching live data for {ticker}..."):
        stock = yf.Ticker(ticker)
        time.sleep(2)
        info = stock.info

    name = info.get('longName', ticker)
    sector = info.get('sector', 'N/A')
    industry = info.get('industry', 'N/A')
    current_price = info.get('currentPrice', 0)
    revenue = info.get('totalRevenue', 0)
    net_income = info.get('netIncomeToCommon', 0)
    market_cap = info.get('marketCap', 0)

    st.subheader(name)
    st.caption(f"Sector: {sector}   |   Industry: {industry}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Price", f"${current_price:,.2f}")
    col2.metric("Revenue", format_value(revenue))
    col3.metric("Net Income", format_value(net_income))
    col4.metric("Market Cap", format_value(market_cap))

    st.divider()
    st.subheader("DCF Assumptions")
    st.caption("Adjust the sliders below to model different scenarios")

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        growth_rate = st.slider("Revenue Growth Rate (%)", 0, 30, 10) / 100
    with col_b:
        discount_rate = st.slider("Discount Rate / WACC (%)", 5, 20, 10) / 100
    with col_c:
        terminal_growth = st.slider("Terminal Growth Rate (%)", 0, 5, 2) / 100
    with col_d:
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

        pv_fcf_total = sum(pv_fcfs)
        terminal_value = projected_fcf[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / (1 + discount_rate) ** years
        enterprise_value = pv_fcf_total + pv_terminal
        shares = info.get('sharesOutstanding', 1)
        intrinsic_value = enterprise_value / shares
        upside = ((intrinsic_value - current_price) / current_price) * 100 if current_price else 0

        st.divider()
        st.subheader("Projected vs Present Value of Free Cash Flows")
        st.caption("Projected FCF = raw future cash flow | PV of FCF = discounted back to today's dollars")

        chart_data = pd.DataFrame({
            "Projected FCF": [cf / 1e9 for cf in projected_fcf],
            "PV of FCF (Discounted)": [pv / 1e9 for pv in pv_fcfs]
        }, index=[f"Year {i}" for i in range(1, years + 1)])

        st.bar_chart(chart_data, color=["#63b3ed", "#68d391"])
        st.caption("Values in billions (USD)")

        st.divider()
        st.subheader("DCF Output")

        col4, col5, col6, col7 = st.columns(4)
        col4.metric("PV of FCFs", format_value(pv_fcf_total))
        col5.metric("PV of Terminal Value", format_value(pv_terminal))
        col6.metric("Enterprise Value", format_value(enterprise_value))
        col7.metric("Intrinsic Value / Share", f"${intrinsic_value:.2f}")

        st.divider()
        if upside > 0:
            st.success(f"Upside vs Current Price: +{upside:.1f}% — Stock appears UNDERVALUED at current DCF assumptions")
        else:
            st.error(f"Downside vs Current Price: {upside:.1f}% — Stock appears OVERVALUED at current DCF assumptions")

        st.divider()
        st.subheader("Valuation Summary Table")
        summary = pd.DataFrame({
            "Metric": ["Current Market Price", "DCF Intrinsic Value", "Enterprise Value", "Market Cap", "Upside / Downside"],
            "Value": [
                f"${current_price:.2f}",
                f"${intrinsic_value:.2f}",
                format_value(enterprise_value),
                format_value(market_cap),
                f"{upside:+.1f}%"
            ]
        })
        st.table(summary)

    else:
        st.warning("No free cash flow data available for this ticker.")