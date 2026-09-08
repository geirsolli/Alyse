import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Aksjeanalyse V2", page_icon="📈", layout="wide")

st.title("📈 Aksjeanalyse V2")
st.caption("Analyser enkeltaksjer og ranger et utvalg Oslo Børs-aksjer. Ikke investeringsråd.")

OSLO_DEFAULT = [
    "EQNR.OL", "DNB.OL", "KOG.OL", "NHY.OL", "TEL.OL",
    "ORK.OL", "MOWI.OL", "YAR.OL", "AKRBP.OL", "SALM.OL",
    "TOM.OL", "SUBC.OL", "AUSS.OL", "BWLPG.OL", "FRO.OL",
    "GJF.OL", "STB.OL", "TGS.OL", "SCHA.OL", "BAKKA.OL"
]

@st.cache_data(ttl=900, show_spinner=False)
def get_history(ticker: str, period: str = "1y"):
    try:
        hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        return hist
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def get_info(ticker: str):
    try:
        return yf.Ticker(ticker).info
    except Exception:
        return {}

def safe_num(v):
    return v if isinstance(v, (int, float, np.integer, np.floating)) and np.isfinite(v) else None

def analyze_ticker(ticker: str, include_fundamentals: bool = True):
    hist = get_history(ticker, "1y")
    if hist is None or hist.empty or "Close" not in hist.columns:
        return None

    close = hist["Close"].dropna()
    if len(close) < 60:
        return None

    current = float(close.iloc[-1])
    ret_1y = (current / float(close.iloc[0]) - 1) * 100

    if len(close) >= 126:
        ret_6m = (current / float(close.iloc[-126]) - 1) * 100
    else:
        ret_6m = np.nan

    ma50 = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else np.nan

    daily = close.pct_change().dropna()
    vol = daily.std() * np.sqrt(252) * 100 if len(daily) > 1 else np.nan

    high_52w = float(close.max())
    drawdown_from_high = (current / high_52w - 1) * 100 if high_52w else np.nan

    info = get_info(ticker) if include_fundamentals else {}
    pe = safe_num(info.get("trailingPE"))
    name = info.get("shortName") or info.get("longName") or ticker
    currency = info.get("currency") or ""

    score = 0.0
    max_score = 100.0
    reasons = []

    # Trend: 30 poeng
    if np.isfinite(ma200):
        if current > ma200:
            score += 18
            reasons.append("Kurs over 200-dagers snitt")
        if np.isfinite(ma50) and ma50 > ma200:
            score += 12
            reasons.append("50-dagers snitt over 200-dagers snitt")
    else:
        if np.isfinite(ma50) and current > ma50:
            score += 15
            reasons.append("Kurs over 50-dagers snitt")

    # Momentum: 30 poeng
    if ret_1y > 25:
        score += 18
    elif ret_1y > 10:
        score += 14
    elif ret_1y > 0:
        score += 8

    if np.isfinite(ret_6m):
        if ret_6m > 15:
            score += 12
        elif ret_6m > 5:
            score += 9
        elif ret_6m > 0:
            score += 5

    # Risiko: 20 poeng
    if np.isfinite(vol):
        if vol < 20:
            score += 20
        elif vol < 30:
            score += 15
        elif vol < 40:
            score += 9
        elif vol < 55:
            score += 4

    # Verdsettelse: 20 poeng
    if pe is not None and pe > 0:
        if pe < 12:
            score += 20
        elif pe < 18:
            score += 16
        elif pe < 25:
            score += 10
        elif pe < 35:
            score += 5
    else:
        # Ikke straff aksjen fullt når P/E mangler
        max_score = 80.0

    normalized = round(score / max_score * 100, 1) if max_score else 0

    return {
        "Ticker": ticker,
        "Selskap": name,
        "Kurs": current,
        "Valuta": currency,
        "1 år %": ret_1y,
        "6 mnd %": ret_6m,
        "Volatilitet %": vol,
        "Fra 52u topp %": drawdown_from_high,
        "P/E": pe,
        "Score": normalized,
        "MA50": float(ma50) if np.isfinite(ma50) else np.nan,
        "MA200": float(ma200) if np.isfinite(ma200) else np.nan,
        "_history": hist,
        "_reasons": reasons,
    }

def score_label(score):
    if score >= 80:
        return "Sterk"
    if score >= 65:
        return "Interessant"
    if score >= 50:
        return "Nøytral"
    return "Svak"

tab1, tab2 = st.tabs(["🔎 Enkeltanalyse", "🏆 Oslo Børs-rangering"])

with tab1:
    ticker = st.text_input(
        "Ticker",
        value="EQNR.OL",
        help="Norske aksjer bruker vanligvis .OL, f.eks. EQNR.OL eller DNB.OL.",
        key="single_ticker",
    ).strip().upper()

    if st.button("Analyser aksje", type="primary", key="single_btn"):
        with st.spinner(f"Analyserer {ticker}..."):
            r = analyze_ticker(ticker, include_fundamentals=True)

        if r is None:
            st.error("Fant ikke nok data. Sjekk tickeren.")
        else:
            st.subheader(f"{r['Selskap']} ({r['Ticker']})")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Kurs", f"{r['Kurs']:.2f} {r['Valuta']}")
            c2.metric("1 år", f"{r['1 år %']:.1f}%")
            c3.metric("P/E", f"{r['P/E']:.1f}" if r["P/E"] is not None else "N/A")
            c4.metric("Score", f"{r['Score']:.0f}/100")

            st.progress(min(max(r["Score"] / 100, 0), 1))

            chart = r["_history"][["Close"]].copy()
            chart["MA50"] = chart["Close"].rolling(50).mean()
            if len(chart) >= 200:
                chart["MA200"] = chart["Close"].rolling(200).mean()
            st.line_chart(chart)

            left, right = st.columns(2)
            with left:
                st.markdown("### Nøkkeltall")
                data = [
                    ["6 mnd. avkastning", f"{r['6 mnd %']:.1f}%" if np.isfinite(r["6 mnd %"]) else "N/A"],
                    ["Årlig volatilitet", f"{r['Volatilitet %']:.1f}%"],
                    ["Fra 52-ukers topp", f"{r['Fra 52u topp %']:.1f}%"],
                    ["MA50", f"{r['MA50']:.2f}" if np.isfinite(r["MA50"]) else "N/A"],
                    ["MA200", f"{r['MA200']:.2f}" if np.isfinite(r["MA200"]) else "N/A"],
                ]
                st.dataframe(pd.DataFrame(data, columns=["Måltall", "Verdi"]), hide_index=True, use_container_width=True)

            with right:
                st.markdown("### Vurdering")
                st.write(f"**Kategori:** {score_label(r['Score'])}")
                if r["_reasons"]:
                    for x in r["_reasons"]:
                        st.write(f"✅ {x}")
                st.caption("Scoren kombinerer trend, momentum, volatilitet og P/E når P/E er tilgjengelig.")

with tab2:
    st.markdown("### Ranger aksjer")
    st.write("Appen analyserer et forhåndsvalgt utvalg Oslo Børs-aksjer og sorterer dem etter score.")

    tickers_text = st.text_area(
        "Tickere",
        value=", ".join(OSLO_DEFAULT),
        height=120,
        help="Du kan legge til eller fjerne tickere. Skill dem med komma.",
    )

    col_a, col_b = st.columns([1, 2])
    with col_a:
        max_stocks = st.slider("Maks antall aksjer", 5, 30, 20)
    with col_b:
        include_fundamentals = st.checkbox(
            "Ta med P/E i rangeringen",
            value=True,
            help="Kan gjøre analysen tregere fordi selskapsdata må hentes for hver aksje.",
        )

    if st.button("Kjør Oslo Børs-rangering", type="primary"):
        tickers = [x.strip().upper() for x in tickers_text.replace("\n", ",").split(",") if x.strip()]
        tickers = list(dict.fromkeys(tickers))[:max_stocks]

        results = []
        progress = st.progress(0)
        status = st.empty()

        for i, t in enumerate(tickers):
            status.write(f"Analyserer {t} ({i+1}/{len(tickers)})...")
            r = analyze_ticker(t, include_fundamentals=include_fundamentals)
            if r:
                results.append(r)
            progress.progress((i + 1) / len(tickers))

        status.empty()

        if not results:
            st.error("Ingen aksjer kunne analyseres.")
        else:
            df = pd.DataFrame(results)
            df["Vurdering"] = df["Score"].apply(score_label)
            df = df.sort_values("Score", ascending=False).reset_index(drop=True)
            df.index = df.index + 1

            show_cols = [
                "Ticker", "Selskap", "Score", "Vurdering", "Kurs",
                "1 år %", "6 mnd %", "Volatilitet %", "P/E"
            ]
            display = df[show_cols].copy()

            for col in ["Score", "Kurs", "1 år %", "6 mnd %", "Volatilitet %", "P/E"]:
                display[col] = pd.to_numeric(display[col], errors="coerce").round(1)

            st.success(f"Analyserte {len(df)} aksjer.")
            st.dataframe(display, use_container_width=True)

            st.markdown("### Topp 5 akkurat nå")
            top = df.head(5)
            for rank, (_, row) in enumerate(top.iterrows(), start=1):
                pe_text = f"P/E {row['P/E']:.1f}" if pd.notna(row["P/E"]) else "P/E N/A"
                st.write(
                    f"**{rank}. {row['Ticker']} — {row['Score']:.0f}/100**  "
                    f"| 1 år {row['1 år %']:.1f}% | Vol. {row['Volatilitet %']:.1f}% | {pe_text}"
                )

            csv = display.to_csv(index=True).encode("utf-8")
            st.download_button(
                "Last ned rangering som CSV",
                data=csv,
                file_name="oslo_bors_rangering.csv",
                mime="text/csv",
            )

st.markdown("---")
st.caption(
    "Viktig: Historisk kursutvikling og en mekanisk score kan ikke forutsi fremtidig avkastning. "
    "Bruk dette som et analyseverktøy, ikke som automatisk kjøps- eller salgsråd."
)
