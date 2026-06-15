import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="DCF Valuation Dashboard", layout="wide", page_icon="💹")

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    
    h1 { color: #0f172a !important; font-size: 2rem !important; font-weight: 700 !important; }
    h2, h3 { color: #1e293b !important; font-weight: 600 !important; }
    
    .stCaption, .caption-text { color: #475569 !important; font-size: 0.85rem !important; font-weight: 500 !important; }
    
    div[data-testid="stMetricLabel"] { 
        color: #475569 !important; font-size: 0.8rem !important; 
        font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.05em !important;
    }
    div[data-testid="stMetricValue"] { color: #0f172a !important; font-size: 1.6rem !important; font-weight: 700 !important; }
    
    div[data-testid="metric-container"] {
        background: #ffffff !important; border-radius: 12px !important;
        padding: 1.2rem 1.5rem !important; border: 1px solid #e2e8f0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    }
    
    .stTextInput > div > div > input {
        background: #ffffff !important; border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important; color: #0f172a !important;
        font-size: 1rem !important; font-weight: 500 !important;
        padding: 0.6rem 1rem !important;
    }
    
    .stSlider > label { color: #334155 !important; font-weight: 600 !important; font-size: 0.85rem !important; }
    
    .header-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        padding: 2rem 2.5rem; border-radius: 16px; margin-bottom: 2rem;
    }
    .header-banner h1 { color: #ffffff !important; margin: 0 !important; }
    .header-banner p { color: #94a3b8 !important; margin: 0.3rem 0 0 0 !important; font-size: 0.9rem !important; font-weight: 500 !important; }
    
    .section-label {
        color: #64748b !important; font-size: 0.75rem !important;
        font-weight: 700 !important; text-transform: uppercase !important;
        letter-spacing: 0.08em !important; margin-bottom: 0.5rem !important;
    }

    .stSuccess { background: #f0fdf4 !important; border: 1px solid #86efac !important; color: #166534 !important; border-radius: 10px !important; }
    .stError { background: #fff1f2 !important; border: 1px solid #fda4af !important; color: #9f1239 !important; border-radius: 10px !important; }
    .stWarning { background: #fffbeb !important; border: 1px solid #fcd34d !important; color: #92400e !important; border-radius: 10px !important; }

    thead tr th { background: #f1f5f9 !important; color: #334155 !important; font-weight: 700 !important; font-size: 0.85rem !important; }
    tbody tr td { color: #1e293b !important; font-size: 0.9rem !important; }
    tbody tr:nth-child(even) { background: #f8fafc !important; }
    tbody tr:nth-child(odd) { background: #ffffff !important; }

    hr { border-color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-banner">
    <h1>DCF Valuation Dashboard</h1>
    <p>Built by Rishi Bhandari &nbsp;|&nbsp; Live market data via yfinance</p>
</div>
""", unsafe_allow_html=True)

ticker = st.text_input("Stock Ticker", value="AAPL", placeholder="e.g. AAPL, TSLA, MSFT").upper()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_info(symbol):
    """Fetch company info once per ticker per hour. Retries with backoff on rate limits."""
    last_err = None
    for attempt in range(3):
        try:
            data = yf.Ticker(symbol).info
            # Yahoo sometimes returns a near-empty dict for bad/unknown tickers
            if not data or data.get("currentPrice") is None and data.get("regularMarketPrice") is None:
                return None
            return data
        except Exception as e:
            last_err = e
            time.sleep(2 ** attempt)  # 1s, 2s, 4s backoff
    raise last_err

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
        try:
            info = fetch_info(ticker)
        except yf.exceptions.YFRateLimitError:
            st.error("Yahoo Finance is rate-limiting requests right now (this is common on free shared hosting). Please wait a minute and try again.")
            st.stop()
        except Exception as e:
            st.error(f"Could not fetch data for {ticker}. Yahoo may be temporarily unavailable. Try again shortly.")
            st.stop()

    if info is None:
        st.warning(f"No data found for '{ticker}'. Double-check the ticker symbol (e.g. AAPL, MSFT, TSLA).")
        st.stop()

    name = info.get('longName', ticker)
    sector = info.get('sector', 'N/A')
    industry = info.get('industry', 'N/A')
    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
    revenue = info.get('totalRevenue', 0)
    net_income = info.get('netIncomeToCommon', 0)
    market_cap = info.get('marketCap', 0)

    st.subheader(name)
    st.markdown(f'<p class="section-label">Sector: {sector} &nbsp;|&nbsp; Industry: {industry}</p>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Price", f"${current_price:,.2f}")
    col2.metric("Revenue", format_value(revenue))
    col3.metric("Net Income", format_value(net_income))
    col4.metric("Market Cap", format_value(market_cap))

    st.divider()
    st.subheader("DCF Assumptions")
    st.markdown('<p class="section-label">Adjust the sliders to model different scenarios</p>', unsafe_allow_html=True)

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
        st.markdown('<p class="section-label">Projected FCF = future cash flow &nbsp;|&nbsp; PV of FCF = discounted to today\'s dollars &nbsp;|&nbsp; Values in billions (USD)</p>', unsafe_allow_html=True)

        chart_data = pd.DataFrame({
            "Projected FCF ($B)": [cf / 1e9 for cf in projected_fcf],
            "PV of FCF — Discounted ($B)": [pv / 1e9 for pv in pv_fcfs]
        }, index=[f"Year {i}" for i in range(1, years + 1)])

        st.bar_chart(chart_data, color=["#3b82f6", "#10b981"])

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
        st.subheader("Valuation Summary")
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