import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Aksjeanalyse", page_icon="📈", layout="wide")

st.title("📈 Aksjeanalyse")
st.caption("En enkel analyse-app for aksjer. Dette er et analyseverktøy, ikke investeringsråd.")

@st.cache_data(ttl=900)
def load_history(ticker: str, period: str = "1y"):
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period, auto_adjust=True)
    return hist

@st.cache_data(ttl=3600)
def load_info(ticker: str):
    stock = yf.Ticker(ticker)
    try:
        return stock.info
    except Exception:
        return {}

def analyze_stock(ticker: str):
    hist = load_history(ticker, "1y")
    if hist is None or hist.empty or len(hist) < 20:
        return None

    close = hist["Close"].dropna()
    if close.empty:
        return None

    current_price = float(close.iloc[-1])
    first_price = float(close.iloc[0])
    return_1y = (current_price / first_price - 1) * 100

    ma_50_series = close.rolling(50).mean()
    ma_200_series = close.rolling(200).mean()
    ma_50 = float(ma_50_series.iloc[-1]) if not np.isnan(ma_50_series.iloc[-1]) else None
    ma_200 = float(ma_200_series.iloc[-1]) if not np.isnan(ma_200_series.iloc[-1]) else None

    daily_returns = close.pct_change().dropna()
    annual_volatility = float(daily_returns.std() * np.sqrt(252) * 100) if len(daily_returns) > 1 else None

    info = load_info(ticker)
    pe = info.get("trailingPE")
    market_cap = info.get("marketCap")
    company_name = info.get("longName") or info.get("shortName") or ticker
    currency = info.get("currency") or ""

    score = 0
    max_score = 10
    reasons = []

    # Trend: 4 poeng
    if ma_200 is not None:
        if current_price > ma_200:
            score += 2
            reasons.append("✅ Kursen er over 200-dagers glidende gjennomsnitt.")
        else:
            reasons.append("⚠️ Kursen er under 200-dagers glidende gjennomsnitt.")

    if ma_50 is not None and ma_200 is not None:
        if ma_50 > ma_200:
            score += 2
            reasons.append("✅ 50-dagers snitt ligger over 200-dagers snitt.")
        else:
            reasons.append("⚠️ 50-dagers snitt ligger under 200-dagers snitt.")

    # Avkastning: 2 poeng
    if return_1y > 15:
        score += 2
        reasons.append("✅ Sterk kursutvikling siste 12 måneder.")
    elif return_1y > 0:
        score += 1
        reasons.append("➕ Positiv kursutvikling siste 12 måneder.")
    else:
        reasons.append("⚠️ Negativ kursutvikling siste 12 måneder.")

    # Verdsettelse: 2 poeng
    if isinstance(pe, (int, float)) and pe > 0:
        if pe < 20:
            score += 2
            reasons.append("✅ P/E er under 20.")
        elif pe < 30:
            score += 1
            reasons.append("➕ P/E er mellom 20 og 30.")
        else:
            reasons.append("⚠️ P/E er over 30.")
    else:
        reasons.append("ℹ️ P/E var ikke tilgjengelig.")

    # Risiko: 2 poeng
    if annual_volatility is not None:
        if annual_volatility < 25:
            score += 2
            reasons.append("✅ Relativt lav historisk volatilitet.")
        elif annual_volatility < 40:
            score += 1
            reasons.append("➕ Moderat historisk volatilitet.")
        else:
            reasons.append("⚠️ Høy historisk volatilitet.")

    return {
        "ticker": ticker,
        "company_name": company_name,
        "currency": currency,
        "history": hist,
        "current_price": current_price,
        "return_1y": return_1y,
        "ma_50": ma_50,
        "ma_200": ma_200,
        "volatility": annual_volatility,
        "pe": pe,
        "market_cap": market_cap,
        "score": score,
        "max_score": max_score,
        "reasons": reasons,
    }

with st.sidebar:
    st.header("Innstillinger")
    ticker = st.text_input(
        "Ticker",
        value="EQNR.OL",
        help="Norske aksjer bruker vanligvis .OL, f.eks. DNB.OL, KOG.OL og NHY.OL.",
    ).strip().upper()

    analyze = st.button("Analyser aksje", type="primary", use_container_width=True)

    st.markdown("---")
    st.write("Eksempler:")
    st.code("EQNR.OL\nDNB.OL\nKOG.OL\nNHY.OL\nAAPL\nMSFT")

if analyze or ticker:
    try:
        result = analyze_stock(ticker)

        if result is None:
            st.error("Fant ikke nok kursdata. Sjekk at tickeren er riktig.")
        else:
            st.subheader(f"{result['company_name']} ({result['ticker']})")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Siste kurs", f"{result['current_price']:.2f} {result['currency']}")
            c2.metric("12 mnd. avkastning", f"{result['return_1y']:.1f}%")
            c3.metric("P/E", f"{result['pe']:.1f}" if isinstance(result["pe"], (int, float)) else "Ikke tilgjengelig")
            c4.metric("Score", f"{result['score']}/{result['max_score']}")

            st.progress(result["score"] / result["max_score"])

            st.markdown("### Kursutvikling")
            chart = result["history"][["Close"]].copy()
            if result["ma_50"] is not None:
                chart["MA50"] = chart["Close"].rolling(50).mean()
            if result["ma_200"] is not None:
                chart["MA200"] = chart["Close"].rolling(200).mean()
            st.line_chart(chart)

            left, right = st.columns([1, 1])

            with left:
                st.markdown("### Nøkkeltall")
                rows = [
                    ["Siste kurs", f"{result['current_price']:.2f} {result['currency']}"],
                    ["12 mnd. avkastning", f"{result['return_1y']:.1f}%"],
                    ["50-dagers snitt", f"{result['ma_50']:.2f}" if result["ma_50"] is not None else "Ikke tilgjengelig"],
                    ["200-dagers snitt", f"{result['ma_200']:.2f}" if result["ma_200"] is not None else "Ikke tilgjengelig"],
                    ["Årlig historisk volatilitet", f"{result['volatility']:.1f}%" if result["volatility"] is not None else "Ikke tilgjengelig"],
                    ["P/E", f"{result['pe']:.1f}" if isinstance(result["pe"], (int, float)) else "Ikke tilgjengelig"],
                ]
                st.dataframe(
                    pd.DataFrame(rows, columns=["Måltall", "Verdi"]),
                    hide_index=True,
                    use_container_width=True,
                )

            with right:
                st.markdown("### Hvorfor fikk aksjen denne scoren?")
                for reason in result["reasons"]:
                    st.write(reason)

            st.info(
                "Scoren er en enkel modell basert på historisk trend, avkastning, P/E og volatilitet. "
                "Den bør ikke brukes alene som grunnlag for kjøp eller salg."
            )

    except Exception as e:
        st.error(f"Noe gikk galt: {e}")
        st.caption("Yahoo Finance kan av og til ha midlertidige dataproblemer. Prøv igjen senere eller test en annen ticker.")
