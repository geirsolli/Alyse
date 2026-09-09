import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(
    page_title="Aksjeanalyse Pro V4.1",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    [data-testid="stToolbar"] {display:none !important;}
    [data-testid="stDecoration"] {display:none !important;}
    #MainMenu {visibility:hidden !important;}
    footer {visibility:hidden !important;}
    header {visibility:hidden !important;}
    .block-container {padding-top:0.5rem !important; padding-bottom:2rem !important; max-width:1180px;}
    .stButton > button {min-height:3rem; border-radius:0.8rem; font-weight:600;}
    .stTextInput input, .stTextArea textarea {font-size:16px !important; border-radius:0.75rem !important;}
    @media (max-width:700px) {
        .block-container {padding-left:0.75rem !important; padding-right:0.75rem !important; padding-top:0.2rem !important;}
        h1 {font-size:2.0rem !important;}
        [data-testid="stMetricValue"] {font-size:1.2rem !important;}
        [data-testid="stMetricLabel"] {font-size:0.85rem !important;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Aksjeanalyse Pro")
st.caption("Detaljanalyse og screening av 40 store Oslo Børs-aksjer. Ikke investeringsråd.")

# Kuratert Top 40-liste. Kan redigeres i appen dersom ønskelig.
TOP40 = [
    ("EQNR.OL", "Equinor"),
    ("DNB.OL", "DNB Bank"),
    ("KOG.OL", "Kongsberg Gruppen"),
    ("TEL.OL", "Telenor"),
    ("NHY.OL", "Norsk Hydro"),
    ("AKRBP.OL", "Aker BP"),
    ("MOWI.OL", "Mowi"),
    ("ORK.OL", "Orkla"),
    ("YAR.OL", "Yara"),
    ("SALM.OL", "SalMar"),
    ("TOM.OL", "Tomra"),
    ("SUBC.OL", "Subsea 7"),
    ("FRO.OL", "Frontline"),
    ("GJF.OL", "Gjensidige"),
    ("STB.OL", "Storebrand"),
    ("AUSS.OL", "Austevoll Seafood"),
    ("BWLPG.OL", "BW LPG"),
    ("TGS.OL", "TGS"),
    ("BAKKA.OL", "Bakkafrost"),
    ("SCHA.OL", "Schibsted"),
    ("AKSO.OL", "Aker Solutions"),
    ("ELK.OL", "Elkem"),
    ("HAFNI.OL", "Hafnia"),
    ("LSG.OL", "Lerøy Seafood"),
    ("VAR.OL", "Vår Energi"),
    ("AUTO.OL", "AutoStore"),
    ("SCATC.OL", "Scatec"),
    ("MPCC.OL", "MPC Container Ships"),
    ("GOGL.OL", "Golden Ocean"),
    ("NAS.OL", "Norwegian Air Shuttle"),
    ("NEL.OL", "Nel"),
    ("BORR.OL", "Borr Drilling"),
    ("DOF.OL", "DOF Group"),
    ("DNO.OL", "DNO"),
    ("AFG.OL", "AF Gruppen"),
    ("VEI.OL", "Veidekke"),
    ("KIT.OL", "Kitron"),
    ("ATEA.OL", "Atea"),
    ("CRAYN.OL", "Crayon"),
    ("PROT.OL", "Protector Forsikring"),
]

TOP40_TICKERS = [t for t, _ in TOP40]
TOP40_LABELS = {t: f"{t} — {name}" for t, name in TOP40}

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
    dd = series / series.cummax() - 1
    return float(dd.min() * 100)

def avg_or_nan(values):
    vals = [float(v) for v in values if v is not None and np.isfinite(v)]
    return round(float(np.mean(vals)), 1) if vals else np.nan

def score_label(score):
    if score >= 80: return "Sterk"
    if score >= 65: return "Interessant"
    if score >= 50: return "Nøytral"
    return "Svak"

def fmt(v, suffix="", decimals=1):
    try:
        if v is None or not np.isfinite(float(v)):
            return "N/A"
        return f"{float(v):.{decimals}f}{suffix}"
    except Exception:
        return "N/A"

def analyze_ticker(ticker, full=True):
    hist = get_history(ticker, "2y")
    if hist is None or hist.empty or "Close" not in hist.columns:
        return None

    close = hist["Close"].dropna()
    if len(close) < 220:
        return None

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
    from_high = (current / high_52 - 1) * 100

    info = get_info(ticker) if full else {}
    name = info.get("shortName") or info.get("longName") or dict(TOP40).get(ticker, ticker)
    currency = info.get("currency") or "NOK"

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
    reasons = []
    if current > ma200:
        tech += 20
        reasons.append("Kurs over MA200")
    if ma50 > ma200:
        tech += 15
        reasons.append("MA50 over MA200")
    tech += 15 if ret_6m > 10 else 8 if ret_6m > 0 else 0
    tech += 10 if ret_3m > 5 else 5 if ret_3m > 0 else 0
    if 45 <= rsi14 <= 70:
        tech += 15
        reasons.append("RSI i konstruktivt område")
    elif 30 <= rsi14 < 45 or 70 < rsi14 <= 75:
        tech += 8
    if macd_hist > 0:
        tech += 15
        reasons.append("Positiv MACD")
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

    risk_parts = [
        90 if vol < 20 else 75 if vol < 30 else 55 if vol < 40 else 30,
        90 if mdd > -20 else 70 if mdd > -35 else 50 if mdd > -50 else 25,
    ]
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
        "Fra 52u topp %": from_high, "MA50": ma50, "MA200": ma200,
        "P/E": pe, "Forward P/E": fwd_pe, "P/B": pb, "EV/EBITDA": ev_ebitda,
        "ROE %": roe, "ROA %": roa, "Profit margin %": profit_margin,
        "Operating margin %": op_margin, "Revenue growth %": revenue_growth,
        "Earnings growth %": earnings_growth, "Debt/Equity": debt_to_equity,
        "Current ratio": current_ratio, "Beta": beta, "Dividend yield %": dividend_yield,
        "Fair value proxy": fair_value, "_history": hist, "_reasons": reasons,
    }

# Persist selected ticker across tabs.
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "EQNR.OL"

tab1, tab2, tab3 = st.tabs(["🔬 Enkeltanalyse", "🏆 Top 40", "📋 Tickerliste"])

with tab1:
    st.markdown("### Velg fra Top 40")
    selected_from_list = st.selectbox(
        "Velg aksje",
        options=TOP40_TICKERS,
        index=TOP40_TICKERS.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in TOP40_TICKERS else 0,
        format_func=lambda x: TOP40_LABELS[x],
    )

    if st.button("Bruk valgt ticker", use_container_width=True):
        st.session_state.selected_ticker = selected_from_list

    ticker = st.text_input(
        "Ticker for enkeltanalyse",
        value=st.session_state.selected_ticker,
        help="Du kan også skrive inn en annen ticker manuelt.",
    ).strip().upper()

    if st.button("Kjør avansert analyse", type="primary", use_container_width=True):
        st.session_state.selected_ticker = ticker
        with st.spinner(f"Analyserer {ticker}..."):
            r = analyze_ticker(ticker, full=True)

        if r is None:
            st.error("Fant ikke nok data for denne tickeren.")
        else:
            st.subheader(f"{r['Selskap']} ({r['Ticker']})")
            a, b = st.columns(2)
            a.metric("Kurs", f"{r['Kurs']:.2f} {r['Valuta']}")
            b.metric("Total score", f"{r['Score']:.0f}/100")
            c, d = st.columns(2)
            c.metric("1 år", fmt(r["1 år %"], "%"))
            d.metric("RSI", fmt(r["RSI14"]))
            st.progress(min(max(r["Score"] / 100, 0), 1))

            st.markdown("### Delscorer")
            st.dataframe(pd.DataFrame({
                "Område": ["Teknisk", "Fundamental", "Risiko", "Kvalitet"],
                "Score": [r["Teknisk"], r["Fundamental"], r["Risiko"], r["Kvalitet"]],
            }), hide_index=True, use_container_width=True)

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
                ["Volatilitet", fmt(r["Volatilitet %"], "%")],
                ["Sharpe", fmt(r["Sharpe"])],
                ["Maks drawdown", fmt(r["Maks drawdown %"], "%")],
            ], columns=["Måltall", "Verdi"]), hide_index=True, use_container_width=True)

            st.markdown("### Fundamental")
            st.dataframe(pd.DataFrame([
                ["P/E", fmt(r["P/E"])],
                ["Forward P/E", fmt(r["Forward P/E"])],
                ["P/B", fmt(r["P/B"])],
                ["EV/EBITDA", fmt(r["EV/EBITDA"])],
                ["ROE", fmt(r["ROE %"], "%")],
                ["Resultatmargin", fmt(r["Profit margin %"], "%")],
                ["Omsetningsvekst", fmt(r["Revenue growth %"], "%")],
                ["Resultatvekst", fmt(r["Earnings growth %"], "%")],
                ["Gjeld/Egenkapital", fmt(r["Debt/Equity"])],
                ["Beta", fmt(r["Beta"])],
                ["Direkteavkastning", fmt(r["Dividend yield %"], "%")],
            ], columns=["Måltall", "Verdi"]), hide_index=True, use_container_width=True)

            if r["Fair value proxy"] is not None:
                diff = (r["Fair value proxy"] / r["Kurs"] - 1) * 100
                st.markdown("### Enkel verdiindikasjon")
                st.write(f"Normalisert P/E-proxy: **{r['Fair value proxy']:.2f} {r['Valuta']}** ({diff:+.1f}% mot dagens kurs).")
                st.caption("Dette er ikke et kursmål. Beregningen normaliserer bare dagens resultat mot P/E 18.")

with tab2:
    st.markdown("### Analyser 40 aksjer")
    mode = st.radio(
        "Analysemodus",
        ["Full analyse", "Hurtigmodus"],
        horizontal=True,
        help="Full analyse henter flere fundamentale nøkkeltall. Hurtigmodus er raskere og fokuserer mest på kurs/teknisk data.",
    )
    min_score = st.slider("Vis bare score over", 0, 90, 0, step=5)
    sort_by = st.selectbox("Sorter etter", ["Score", "Direkteavkastning %", "Teknisk", "Fundamental", "Risiko", "Kvalitet", "1 år %"])

    if st.button("Analyser Oslo Børs Top 40", type="primary", use_container_width=True):
        results = []
        progress = st.progress(0)
        status = st.empty()
        full = mode == "Full analyse"

        for i, ticker40 in enumerate(TOP40_TICKERS):
            status.write(f"Analyserer {TOP40_LABELS[ticker40]} ({i+1}/40)...")
            r = analyze_ticker(ticker40, full=full)
            if r:
                results.append(r)
            progress.progress((i + 1) / 40)

        status.empty()

        if not results:
            st.error("Ingen aksjer kunne analyseres.")
        else:
            df = pd.DataFrame(results)
            df["Vurdering"] = df["Score"].apply(score_label)
            df["Direkteavkastning %"] = pd.to_numeric(df["Dividend yield %"], errors="coerce")

            if min_score > 0:
                df = df[df["Score"] >= min_score]

            if sort_by in df.columns:
                df = df.sort_values(sort_by, ascending=False, na_position="last")

            df = df.reset_index(drop=True)
            df.index = df.index + 1

            show_cols = [
                "Ticker", "Selskap", "Score", "Vurdering", "Teknisk",
                "Fundamental", "Risiko", "Kvalitet", "1 år %",
                "Volatilitet %", "Direkteavkastning %", "P/E", "ROE %"
            ]
            display = df[show_cols].copy()
            for col in ["Score", "Teknisk", "Fundamental", "Risiko", "Kvalitet", "1 år %", "Volatilitet %", "Direkteavkastning %", "P/E", "ROE %"]:
                display[col] = pd.to_numeric(display[col], errors="coerce").round(1)

            st.success(f"Analyserte {len(results)} av 40 aksjer.")
            st.dataframe(display, use_container_width=True)

            st.markdown("### Topp 10")
            for rank, (_, row) in enumerate(df.head(10).iterrows(), start=1):
                div_txt = fmt(row["Direkteavkastning %"], "%")
                st.write(f"**{rank}. {row['Ticker']} — {row['Score']:.0f}/100** · {row['Selskap']} · Utbytte {div_txt}")

            st.markdown("### Send ticker til enkeltanalyse")
            if len(df):
                pick = st.selectbox(
                    "Velg en aksje fra resultatlisten",
                    df["Ticker"].tolist(),
                    format_func=lambda x: f"{x} — {df.loc[df['Ticker'] == x, 'Selskap'].iloc[0]}",
                    key="result_pick",
                )
                if st.button("Bruk denne i enkeltanalyse", use_container_width=True):
                    st.session_state.selected_ticker = pick
                    st.success(f"{pick} er valgt. Åpne fanen Enkeltanalyse.")

            csv = display.to_csv(index=True).encode("utf-8")
            st.download_button(
                "Last ned Top 40-resultat som CSV",
                data=csv,
                file_name="oslo_bors_top40_analyse.csv",
                mime="text/csv",
                use_container_width=True,
            )

with tab3:
    st.markdown("### Top 40 tickerliste")
    st.write("Trykk og hold på en ticker på iPhone for å kopiere den, eller velg den direkte i Enkeltanalyse.")
    ticker_df = pd.DataFrame(TOP40, columns=["Ticker", "Selskap"])
    st.dataframe(ticker_df, hide_index=True, use_container_width=True)

    st.markdown("### Kopierbar liste")
    st.code("\n".join(TOP40_TICKERS), language=None)

st.markdown("---")
st.caption(
    "Top 40-listen er en kuratert liste over store/aktive Oslo Børs-selskaper og er ikke en offisiell indeks. "
    "Scoren er mekanisk og kan ikke forutsi fremtidig avkastning."
)
