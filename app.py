import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Aksjeanalyse Pro", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    '''
    <style>
    [data-testid="stToolbar"] {display:none !important;}
    [data-testid="stDecoration"] {display:none !important;}
    #MainMenu {visibility:hidden !important;}
    footer {visibility:hidden !important;}
    header {visibility:hidden !important;}
    .block-container {padding-top:0.6rem !important; padding-bottom:2rem !important; max-width:1150px;}
    .stButton > button {min-height:3rem; border-radius:0.8rem; font-weight:600;}
    .stTextInput input, .stTextArea textarea {font-size:16px !important; border-radius:0.75rem !important;}
    @media (max-width:700px) {
        .block-container {padding-left:0.8rem !important; padding-right:0.8rem !important; padding-top:0.25rem !important;}
        h1 {font-size:2.1rem !important;}
        [data-testid="stMetricValue"] {font-size:1.2rem !important;}
        [data-testid="stMetricLabel"] {font-size:0.85rem !important;}
    }
    </style>
    ''',
    unsafe_allow_html=True,
)

st.title("📊 Aksjeanalyse Pro")
st.caption("Teknisk, fundamental og risikobasert analyse. Ikke investeringsråd.")

OSLO_DEFAULT = [
    "EQNR.OL","DNB.OL","KOG.OL","NHY.OL","TEL.OL","ORK.OL","MOWI.OL","YAR.OL",
    "AKRBP.OL","SALM.OL","TOM.OL","SUBC.OL","AUSS.OL","BWLPG.OL","FRO.OL",
    "GJF.OL","STB.OL","TGS.OL","SCHA.OL","BAKKA.OL"
]

@st.cache_data(ttl=900, show_spinner=False)
def get_history(ticker, period="2y"):
    try:
        return yf.Ticker(ticker).history(period=period, auto_adjust=True)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def get_info(ticker):
    try:
        return yf.Ticker(ticker).info
    except Exception:
        return {}

def safe_num(v):
    try:
        if v is None:
            return None
        v = float(v)
        return v if np.isfinite(v) else None
    except Exception:
        return None

def pct(v):
    x = safe_num(v)
    return x * 100 if x is not None else None

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return float(out.iloc[-1]) if len(out.dropna()) else np.nan

def macd(series):
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    line = ema12 - ema26
    signal = line.ewm(span=9, adjust=False).mean()
    hist = line - signal
    return float(line.iloc[-1]), float(signal.iloc[-1]), float(hist.iloc[-1])

def max_drawdown(series):
    roll = series.cummax()
    dd = series / roll - 1
    return float(dd.min() * 100)

def avg_or_nan(values):
    values = [v for v in values if v is not None and np.isfinite(v)]
    return round(float(np.mean(values)), 1) if values else np.nan

def score_label(score):
    if score >= 80:
        return "Sterk"
    if score >= 65:
        return "Interessant"
    if score >= 50:
        return "Nøytral"
    return "Svak"

def fmt(v, suffix="", decimals=1):
    if v is None:
        return "N/A"
    try:
        if not np.isfinite(float(v)):
            return "N/A"
        return f"{float(v):.{decimals}f}{suffix}"
    except Exception:
        return "N/A"

def analyze_ticker(ticker):
    hist = get_history(ticker, "2y")
    if hist is None or hist.empty or "Close" not in hist.columns:
        return None

    close = hist["Close"].dropna()
    if len(close) < 220:
        return None

    info = get_info(ticker)

    current = float(close.iloc[-1])
    ret_1y = (current / float(close.iloc[-252]) - 1) * 100 if len(close) >= 252 else np.nan
    ret_6m = (current / float(close.iloc[-126]) - 1) * 100
    ret_3m = (current / float(close.iloc[-63]) - 1) * 100
    ma50 = float(close.rolling(50).mean().iloc[-1])
    ma200 = float(close.rolling(200).mean().iloc[-1])

    daily = close.pct_change().dropna()
    vol = float(daily.std() * np.sqrt(252) * 100)
    sharpe = float((daily.mean() / daily.std()) * np.sqrt(252)) if daily.std() != 0 else np.nan
    mdd = max_drawdown(close)
    rsi14 = rsi(close)
    macd_line, macd_signal, macd_hist = macd(close)

    high_52 = float(close.tail(252).max())
    low_52 = float(close.tail(252).min())
    from_high = (current / high_52 - 1) * 100
    from_low = (current / low_52 - 1) * 100

    name = info.get("shortName") or info.get("longName") or ticker
    currency = info.get("currency") or ""
    pe = safe_num(info.get("trailingPE"))
    fwd_pe = safe_num(info.get("forwardPE"))
    pb = safe_num(info.get("priceToBook"))
    ev_ebitda = safe_num(info.get("enterpriseToEbitda"))
    roe = pct(info.get("returnOnEquity"))
    roa = pct(info.get("returnOnAssets"))
    profit_margin = pct(info.get("profitMargins"))
    op_margin = pct(info.get("operatingMargins"))
    revenue_growth = pct(info.get("revenueGrowth"))
    earnings_growth = pct(info.get("earningsGrowth"))
    debt_to_equity = safe_num(info.get("debtToEquity"))
    current_ratio = safe_num(info.get("currentRatio"))
    beta = safe_num(info.get("beta"))
    dividend_yield = pct(info.get("dividendYield"))

    tech = 0
    tech_reasons = []
    if current > ma200:
        tech += 20
        tech_reasons.append("Kurs over MA200")
    if ma50 > ma200:
        tech += 15
        tech_reasons.append("MA50 over MA200")
    if ret_6m > 10:
        tech += 15
    elif ret_6m > 0:
        tech += 8
    if ret_3m > 5:
        tech += 10
    elif ret_3m > 0:
        tech += 5
    if 45 <= rsi14 <= 70:
        tech += 15
        tech_reasons.append("RSI i konstruktivt område")
    elif 30 <= rsi14 < 45 or 70 < rsi14 <= 75:
        tech += 8
    if macd_hist > 0:
        tech += 15
        tech_reasons.append("Positiv MACD")
    if from_high > -10:
        tech += 10
    tech = min(100, round(tech, 1))

    fund_parts = []
    if pe is not None and pe > 0:
        fund_parts.append(95 if pe < 12 else 80 if pe < 18 else 65 if pe < 25 else 45 if pe < 35 else 25)
    if pb is not None and pb > 0:
        fund_parts.append(90 if pb < 1.5 else 70 if pb < 3 else 50 if pb < 5 else 30)
    if ev_ebitda is not None and ev_ebitda > 0:
        fund_parts.append(90 if ev_ebitda < 8 else 70 if ev_ebitda < 12 else 50 if ev_ebitda < 18 else 30)
    if roe is not None:
        fund_parts.append(95 if roe > 20 else 75 if roe > 12 else 55 if roe > 5 else 30)
    if profit_margin is not None:
        fund_parts.append(90 if profit_margin > 20 else 70 if profit_margin > 10 else 55 if profit_margin > 5 else 35)
    if revenue_growth is not None:
        fund_parts.append(90 if revenue_growth > 15 else 70 if revenue_growth > 5 else 55 if revenue_growth > 0 else 30)
    if earnings_growth is not None:
        fund_parts.append(90 if earnings_growth > 15 else 70 if earnings_growth > 5 else 55 if earnings_growth > 0 else 30)
    fundamental = avg_or_nan(fund_parts)

    risk_parts = []
    risk_parts.append(90 if vol < 20 else 75 if vol < 30 else 55 if vol < 40 else 30)
    risk_parts.append(90 if mdd > -20 else 70 if mdd > -35 else 50 if mdd > -50 else 25)
    if beta is not None:
        risk_parts.append(90 if beta < 0.8 else 70 if beta < 1.2 else 50 if beta < 1.6 else 30)
    if debt_to_equity is not None:
        risk_parts.append(90 if debt_to_equity < 50 else 70 if debt_to_equity < 100 else 50 if debt_to_equity < 200 else 30)
    risk = avg_or_nan(risk_parts)

    quality_parts = []
    if roe is not None:
        quality_parts.append(95 if roe > 20 else 75 if roe > 12 else 55 if roe > 5 else 30)
    if op_margin is not None:
        quality_parts.append(90 if op_margin > 20 else 70 if op_margin > 10 else 55 if op_margin > 5 else 35)
    if current_ratio is not None:
        quality_parts.append(85 if current_ratio > 1.5 else 65 if current_ratio > 1.0 else 40)
    quality = avg_or_nan(quality_parts)

    parts, weights = [tech], [0.35]
    if np.isfinite(fundamental):
        parts.append(fundamental); weights.append(0.30)
    if np.isfinite(risk):
        parts.append(risk); weights.append(0.20)
    if np.isfinite(quality):
        parts.append(quality); weights.append(0.15)
    total = round(float(np.average(parts, weights=weights)), 1)

    fair_value = current * 18 / pe if pe is not None and pe > 0 else None

    return {
        "Ticker": ticker, "Selskap": name, "Valuta": currency, "Kurs": current,
        "Score": total, "Teknisk": tech, "Fundamental": fundamental, "Risiko": risk, "Kvalitet": quality,
        "1 år %": ret_1y, "6 mnd %": ret_6m, "3 mnd %": ret_3m,
        "Volatilitet %": vol, "Sharpe": sharpe, "Maks drawdown %": mdd,
        "RSI14": rsi14, "MACD": macd_line, "MACD signal": macd_signal, "MACD hist": macd_hist,
        "Fra 52u topp %": from_high, "Fra 52u bunn %": from_low,
        "MA50": ma50, "MA200": ma200,
        "P/E": pe, "Forward P/E": fwd_pe, "P/B": pb, "EV/EBITDA": ev_ebitda,
        "ROE %": roe, "ROA %": roa, "Profit margin %": profit_margin,
        "Operating margin %": op_margin, "Revenue growth %": revenue_growth,
        "Earnings growth %": earnings_growth, "Debt/Equity": debt_to_equity,
        "Current ratio": current_ratio, "Beta": beta, "Dividend yield %": dividend_yield,
        "Fair value proxy": fair_value, "_history": hist, "_tech_reasons": tech_reasons,
    }

tab1, tab2 = st.tabs(["🔬 Detaljanalyse", "🏆 Rangering"])

with tab1:
    ticker = st.text_input("Ticker", value="EQNR.OL").strip().upper()
    if st.button("Kjør avansert analyse", type="primary", use_container_width=True):
        with st.spinner(f"Analyserer {ticker}..."):
            r = analyze_ticker(ticker)

        if r is None:
            st.error("Fant ikke nok data for denne tickeren.")
        else:
            st.subheader(f"{r['Selskap']} ({r['Ticker']})")
            c1, c2 = st.columns(2)
            c1.metric("Kurs", f"{r['Kurs']:.2f} {r['Valuta']}")
            c2.metric("Total score", f"{r['Score']:.0f}/100")
            c3, c4 = st.columns(2)
            c3.metric("1 år", fmt(r["1 år %"], "%"))
            c4.metric("RSI", fmt(r["RSI14"]))
            st.progress(min(max(r["Score"] / 100, 0), 1))

            st.markdown("### Delscorer")
            st.dataframe(
                pd.DataFrame({
                    "Område": ["Teknisk", "Fundamental", "Risiko", "Kvalitet"],
                    "Score": [r["Teknisk"], r["Fundamental"], r["Risiko"], r["Kvalitet"]],
                }),
                hide_index=True, use_container_width=True
            )

            chart = r["_history"][["Close"]].copy()
            chart["MA50"] = chart["Close"].rolling(50).mean()
            chart["MA200"] = chart["Close"].rolling(200).mean()
            st.line_chart(chart, use_container_width=True)

            st.markdown("### Teknisk")
            st.dataframe(pd.DataFrame([
                ["3 mnd", fmt(r["3 mnd %"], "%")],
                ["6 mnd", fmt(r["6 mnd %"], "%")],
                ["1 år", fmt(r["1 år %"], "%")],
                ["RSI14", fmt(r["RSI14"])],
                ["MACD", fmt(r["MACD"], decimals=3)],
                ["MACD signal", fmt(r["MACD signal"], decimals=3)],
                ["Volatilitet", fmt(r["Volatilitet %"], "%")],
                ["Sharpe", fmt(r["Sharpe"])],
                ["Maks drawdown", fmt(r["Maks drawdown %"], "%")],
                ["Fra 52u topp", fmt(r["Fra 52u topp %"], "%")],
            ], columns=["Måltall","Verdi"]), hide_index=True, use_container_width=True)

            st.markdown("### Fundamental")
            st.dataframe(pd.DataFrame([
                ["P/E", fmt(r["P/E"])],
                ["Forward P/E", fmt(r["Forward P/E"])],
                ["P/B", fmt(r["P/B"])],
                ["EV/EBITDA", fmt(r["EV/EBITDA"])],
                ["ROE", fmt(r["ROE %"], "%")],
                ["ROA", fmt(r["ROA %"], "%")],
                ["Resultatmargin", fmt(r["Profit margin %"], "%")],
                ["Driftsmargin", fmt(r["Operating margin %"], "%")],
                ["Omsetningsvekst", fmt(r["Revenue growth %"], "%")],
                ["Resultatvekst", fmt(r["Earnings growth %"], "%")],
                ["Gjeld/Egenkapital", fmt(r["Debt/Equity"])],
                ["Current ratio", fmt(r["Current ratio"])],
                ["Beta", fmt(r["Beta"])],
                ["Direkteavkastning", fmt(r["Dividend yield %"], "%")],
            ], columns=["Måltall","Verdi"]), hide_index=True, use_container_width=True)

            st.markdown("### Enkel verdiindikasjon")
            if r["Fair value proxy"] is not None:
                diff = (r["Fair value proxy"] / r["Kurs"] - 1) * 100
                st.write(f"Normalisert P/E-proxy: **{r['Fair value proxy']:.2f} {r['Valuta']}** ({diff:+.1f}% mot dagens kurs).")
                st.caption("Dette er ikke et kursmål eller en DCF. Den normaliserer bare dagens resultat mot P/E 18.")
            else:
                st.write("Ikke tilgjengelig fordi P/E mangler eller er negativ.")

            st.markdown("### Oppsummering")
            st.write(f"**Vurdering:** {score_label(r['Score'])}")
            for reason in r["_tech_reasons"]:
                st.write(f"✅ {reason}")

with tab2:
    st.markdown("### Avansert Oslo Børs-rangering")
    tickers_text = st.text_area("Tickere", value=", ".join(OSLO_DEFAULT), height=135)
    max_stocks = st.slider("Maks antall aksjer", 5, 30, 20)

    if st.button("Kjør rangering", type="primary", use_container_width=True):
        tickers = [x.strip().upper() for x in tickers_text.replace("\n", ",").split(",") if x.strip()]
        tickers = list(dict.fromkeys(tickers))[:max_stocks]

        results = []
        progress = st.progress(0)
        status = st.empty()

        for i, t in enumerate(tickers):
            status.write(f"Analyserer {t} ({i+1}/{len(tickers)})...")
            r = analyze_ticker(t)
            if r:
                results.append(r)
            progress.progress((i + 1) / len(tickers))

        status.empty()

        if not results:
            st.error("Ingen aksjer kunne analyseres.")
        else:
            df = pd.DataFrame(results).sort_values("Score", ascending=False).reset_index(drop=True)
            df.index = df.index + 1
            df["Vurdering"] = df["Score"].apply(score_label)

            cols = ["Ticker","Selskap","Score","Vurdering","Teknisk","Fundamental","Risiko","Kvalitet","1 år %","Volatilitet %","P/E","ROE %"]
            display = df[cols].copy()
            for col in ["Score","Teknisk","Fundamental","Risiko","Kvalitet","1 år %","Volatilitet %","P/E","ROE %"]:
                display[col] = pd.to_numeric(display[col], errors="coerce").round(1)

            st.dataframe(display, use_container_width=True)
            st.markdown("### Topp 5")
            for rank, (_, row) in enumerate(df.head(5).iterrows(), start=1):
                fscore = f"{row['Fundamental']:.0f}" if pd.notna(row["Fundamental"]) else "N/A"
                st.write(f"**{rank}. {row['Ticker']} — {row['Score']:.0f}/100** | Teknisk {row['Teknisk']:.0f} | Fundamental {fscore}")

            csv = display.to_csv(index=True).encode("utf-8")
            st.download_button("Last ned rangering som CSV", data=csv, file_name="avansert_oslo_bors_rangering.csv", mime="text/csv", use_container_width=True)

st.markdown("---")
st.caption("Scoren er en mekanisk modell basert på historiske markedsdata og tilgjengelige nøkkeltall. Den kan ta feil og bør ikke brukes alene som kjøps- eller salgsgrunnlag.")
