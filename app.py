import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import urllib.request
import urllib.parse
import html as html_lib
import re

st.set_page_config(
    page_title="Smart Aksjeanalyse",
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
        [data-testid="stDataFrame"] {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }
</style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Smart Aksjeanalyse")
st.caption("Detaljanalyse og screening av store aksjer i Norge, Sverige, Danmark, Finland og USA. Ikke investeringsråd.")

# Kuraterte markedslister. Oslo-listen er den opprinnelige Top 50-listen.
OSLO = [
    ("EQNR.OL", "Equinor"),
    ("DNB.OL", "DNB Bank"),
    ("KOG.OL", "Kongsberg Gruppen"),
    ("AKRBP.OL", "Aker BP"),
    ("NHY.OL", "Norsk Hydro"),
    ("TEL.OL", "Telenor"),
    ("GJF.OL", "Gjensidige"),
    ("VAR.OL", "Vår Energi"),
    ("AKER.OL", "Aker"),
    ("YAR.OL", "Yara"),
    ("MOWI.OL", "Mowi"),
    ("SUBC.OL", "Subsea 7"),
    ("FRO.OL", "Frontline"),
    ("ORK.OL", "Orkla"),
    ("STB.OL", "Storebrand"),
    ("SB1NO.OL", "SpareBank 1 Sør-Norge"),
    ("SALM.OL", "SalMar"),
    ("WAWI.OL", "Wallenius Wilhelmsen"),
    ("AUTO.OL", "AutoStore"),
    ("VEND.OL", "Vend Marketplaces"),
    ("SCHB.OL", "Schibsted B"),
    ("HAFNI.OL", "Hafnia"),
    ("PROT.OL", "Protector Forsikring"),
    ("OLT.OL", "Olav Thon Eiendomsselskap"),
    ("NOD.OL", "Nordic Semiconductor"),
    ("BWLPG.OL", "BW LPG"),
    ("SCHA.OL", "Schibsted A"),
    ("HAUTO.OL", "Höegh Autoliners"),
    ("DOFG.OL", "DOF Group"),
    ("MING.OL", "SpareBank 1 SMN"),
    ("TOM.OL", "Tomra"),
    ("VEI.OL", "Veidekke"),
    ("SPOL.OL", "SpareBank 1 Østlandet"),
    ("TGS.OL", "TGS"),
    ("WWI.OL", "Wilh. Wilhelmsen Holding A"),
    ("BAKKA.OL", "Bakkafrost"),
    ("LSG.OL", "Lerøy Seafood"),
    ("ELK.OL", "Elkem"),
    ("ODL.OL", "Odfjell Drilling"),
    ("KIT.OL", "Kitron"),
    ("OET.OL", "Okeanis Eco Tankers"),
    ("AFG.OL", "AF Gruppen"),
    ("CADLR.OL", "Cadeler"),
    ("AKSO.OL", "Aker Solutions"),
    ("ATEA.OL", "Atea"),
    ("ENTRA.OL", "Entra"),
    ("DNO.OL", "DNO"),
    ("SNI.OL", "Stolt-Nielsen"),
    ("SVEG.OL", "Sparebanken Vest"),
    ("NONG.OL", "SpareBank 1 Nord-Norge")
]

SWEDEN = [
    ("VOLV-B.ST","Volvo B"),("INVE-B.ST","Investor B"),("ATCO-A.ST","Atlas Copco A"),
    ("ABB.ST","ABB"),("ASSA-B.ST","ASSA ABLOY B"),("ERIC-B.ST","Ericsson B"),
    ("SEB-A.ST","SEB A"),("SWED-A.ST","Swedbank A"),("SHB-A.ST","Handelsbanken A"),
    ("SAND.ST","Sandvik"),("ALFA.ST","Alfa Laval"),("EVO.ST","Evolution"),
    ("SAAB-B.ST","Saab B"),("HM-B.ST","H&M B"),("TELIA.ST","Telia"),
    ("HEXA-B.ST","Hexagon B"),("ESSITY-B.ST","Essity B"),("SKF-B.ST","SKF B"),
    ("BOL.ST","Boliden"),("SCA-B.ST","SCA B"),("NIBE-B.ST","Nibe B"),
    ("SINCH.ST","Sinch"),("ELUX-B.ST","Electrolux B"),("GETI-B.ST","Getinge B"),
    ("TEL2-B.ST","Tele2 B"),("LIFCO-B.ST","Lifco B"),("INDU-C.ST","Industrivärden C"),
    ("EQT.ST","EQT"),("LATO-B.ST","Latour B"),("SWEC-B.ST","Sweco B")
]
DENMARK = [
    ("NOVO-B.CO","Novo Nordisk B"),("DSV.CO","DSV"),("MAERSK-B.CO","A.P. Møller-Mærsk B"),
    ("DANSKE.CO","Danske Bank"),("VWS.CO","Vestas Wind Systems"),("ORSTED.CO","Ørsted"),
    ("CARL-B.CO","Carlsberg B"),("COLO-B.CO","Coloplast B"),("PNDORA.CO","Pandora"),
    ("NZYM-B.CO","Novonesis B"),("DEMANT.CO","Demant"),("GMAB.CO","Genmab"),
    ("JYSK.CO","Jyske Bank"),("ROCK-B.CO","Rockwool B"),("TRYG.CO","Tryg"),
    ("GN.CO","GN Store Nord"),("FLS.CO","FLSmidth"),("RBREW.CO","Royal Unibrew"),
    ("AMBU-B.CO","Ambu B"),("ALK-B.CO","ALK-Abelló B")
]
FINLAND = [
    ("NOKIA.HE","Nokia"),("KNEBV.HE","KONE B"),("SAMPO.HE","Sampo"),
    ("NESTE.HE","Neste"),("FORTUM.HE","Fortum"),("UPM.HE","UPM-Kymmene"),
    ("WRT1V.HE","Wärtsilä"),("STERV.HE","Stora Enso R"),("NDA-FI.HE","Nordea Bank"),
    ("ELISA.HE","Elisa"),("KESKOB.HE","Kesko B"),("METSO.HE","Metso"),
    ("ORNBV.HE","Orion B"),("KCR.HE","Konecranes"),("HUH1V.HE","Huhtamäki"),
    ("VALMT.HE","Valmet"),("TIETO.HE","Tietoevry"),("OUT1V.HE","Outokumpu"),
    ("KEMIRA.HE","Kemira"),("CTY1S.HE","Citycon")
]
USA = [
    ("AAPL","Apple"),("MSFT","Microsoft"),("NVDA","NVIDIA"),("AMZN","Amazon"),
    ("GOOGL","Alphabet A"),("META","Meta Platforms"),("BRK-B","Berkshire Hathaway B"),
    ("AVGO","Broadcom"),("TSLA","Tesla"),("JPM","JPMorgan Chase"),("WMT","Walmart"),
    ("LLY","Eli Lilly"),("V","Visa"),("MA","Mastercard"),("XOM","Exxon Mobil"),
    ("COST","Costco"),("NFLX","Netflix"),("JNJ","Johnson & Johnson"),("ORCL","Oracle"),
    ("HD","Home Depot"),("PG","Procter & Gamble"),("BAC","Bank of America"),
    ("ABBV","AbbVie"),("KO","Coca-Cola"),("CRM","Salesforce"),("CVX","Chevron"),
    ("AMD","AMD"),("CSCO","Cisco"),("IBM","IBM"),("GE","GE Aerospace"),
    ("CAT","Caterpillar"),("MRK","Merck"),("MCD","McDonald's"),("DIS","Disney"),
    ("PEP","PepsiCo"),("TMO","Thermo Fisher"),("AXP","American Express"),
    ("GS","Goldman Sachs"),("RTX","RTX"),("QCOM","Qualcomm"),("INTU","Intuit"),
    ("AMGN","Amgen"),("TXN","Texas Instruments"),("ISRG","Intuitive Surgical"),
    ("BKNG","Booking Holdings"),("SPGI","S&P Global"),("BLK","BlackRock"),
    ("PFE","Pfizer"),("LOW","Lowe's"),("UBER","Uber")
]

MARKETS = {
    "🇳🇴 Oslo Børs": OSLO,
    "🇸🇪 Stockholm": SWEDEN,
    "🇩🇰 København": DENMARK,
    "🇫🇮 Helsinki": FINLAND,
    "🇺🇸 USA": USA,
}

selected_market = st.selectbox("🌍 Velg børs / marked", list(MARKETS.keys()), key="selected_market")
TOP50 = MARKETS[selected_market]
TOP50_TICKERS = [t for t, _ in TOP50]
TOP50_LABELS = {t: f"{t} — {name}" for t, name in TOP50}
MARKET_CAP_RANK = {t: i for i, (t, _) in enumerate(TOP50, start=1)}
MARKET_NAME = selected_market.split(" ", 1)[1]
N_STOCKS = len(TOP50)

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


def _html_text(raw):
    raw = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html_lib.unescape(raw)).strip()

def _euronext_fetch(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; SmartAksjeanalyse/6.4)",
            "Accept-Language": "en,nb;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        return r.read().decode("utf-8", errors="ignore")

@st.cache_data(ttl=21600, show_spinner=False)
def get_euronext_insider_data(ticker):
    """Best-effort lesing av offentlige Euronext-meldinger for Oslo.
    Bare tydelige primærinnsider-meldinger tas med. Feil gir None og påvirker ikke score.
    """
    if not ticker.endswith(".OL"):
        return None
    symbol = ticker.replace(".OL", "")
    try:
        search_url = (
            "https://live.euronext.com/en/markets/oslo/equities/company-news-archive"
            "?combine=" + urllib.parse.quote(symbol)
        )
        raw = _euronext_fetch(search_url)

        # Finn detaljlenker til selskapsmeldinger på resultatsiden.
        links = re.findall(
            r'href=["\']([^"\']*/(?:en|nb)/products/equities/company-news/[^"\']+)["\']',
            raw, flags=re.I
        )
        if not links:
            links = re.findall(
                r'href=["\']([^"\']*/(?:en|nb)/products/equities/company-news/20[^"\']+)["\']',
                raw, flags=re.I
            )
        # Unike lenker, maks 12 for å holde analysen rask.
        unique=[]
        for u in links:
            u=html_lib.unescape(u)
            if u not in unique:
                unique.append(u)
        rows=[]
        for u in unique[:12]:
            if u.startswith("/"):
                u="https://live.euronext.com"+u
            try:
                detail=_euronext_fetch(u)
                txt=_html_text(detail)
                low=txt.lower()
                if not any(k in low for k in [
                    "mandatory notification of trade",
                    "primary insider",
                    "meldepliktig handel",
                    "primærinnsider",
                ]):
                    continue
                # Verifiser symbol når Euronext-siden oppgir det.
                sm=re.search(r"\bSymbol\s+([A-Z0-9.-]+)", txt, flags=re.I)
                if sm and sm.group(1).upper() != symbol.upper():
                    continue
                # Ikke la tildelinger/opsjoner mv. bli tolket som ordinære kjøp.
                excluded=["option","award","grant","gift","restricted","rsu","exercise",
                          "conversion","vesting","borrowed","redelivery","share buy-back",
                          "buyback program","tilbakekjøp av egne"]
                if any(k in low for k in excluded):
                    continue
                action=None
                if any(k in low for k in [" has purchased "," purchased "," has bought "," acquired ",
                                          " kjøpt "," har kjøpt "," ervervet "]):
                    action="purchase"
                elif any(k in low for k in [" has sold "," sold "," disposed ",
                                            " solgt "," har solgt "," avhendet "]):
                    action="sale"
                if not action:
                    continue
                dm=re.search(r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+20\d{2})\b",
                             txt, flags=re.I)
                dt=pd.to_datetime(dm.group(1), errors="coerce") if dm else pd.NaT
                if pd.isna(dt):
                    continue
                rows.append({
                    "Date": pd.Timestamp(dt),
                    "Transaction": action,
                    "Text": txt[:3000],
                    "Source": "Euronext Oslo Børs",
                    "URL": u,
                })
            except Exception:
                continue
        return pd.DataFrame(rows) if rows else None
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_yahoo_insider_data(ticker):
    try:
        tx = yf.Ticker(ticker).insider_transactions
        if tx is None or len(tx) == 0:
            return None
        tx=tx.reset_index(drop=True).copy()
        tx["Source"]="Yahoo/yfinance"
        return tx
    except Exception:
        return None

def get_insider_data(ticker):
    # Oslo: Euronext er primærkilde. Yahoo brukes som reserve.
    if ticker.endswith(".OL"):
        eu=get_euronext_insider_data(ticker)
        if eu is not None and len(eu):
            return eu
    return get_yahoo_insider_data(ticker)

def score_insider_activity(tx):
    if tx is None or len(tx) == 0:
        return None, 0, 0, None
    now=pd.Timestamp.now(tz=None); bp=sp=0.0; buys90=sells90=0; latest=None
    for _,row in tx.iterrows():
        txt=" ".join(str(v) for v in row.values if pd.notna(v)).lower()
        if any(k in txt for k in ["option","award","grant","gift","restricted","rsu","exercise","conversion","vesting","borrowed","redelivery"]): continue
        dt=None
        for col in ["Start Date","Date","Transaction Date"]:
            if col in row.index and pd.notna(row[col]):
                try: dt=pd.Timestamp(row[col]).tz_localize(None); break
                except Exception: pass
        if dt is None: continue
        days=max(0,(now.normalize()-dt.normalize()).days)
        if days>365: continue
        latest=dt if latest is None or dt>latest else latest
        action = str(row.get("Transaction", "")).lower() if hasattr(row, "get") else ""
        buy = action == "purchase" or any(k in txt for k in ["purchase","buy","bought","acquisition"])
        sell = action == "sale" or any(k in txt for k in ["sale","sell","sold","disposition"])
        if not (buy or sell): continue
        rec=1.0 if days<=30 else 0.75 if days<=90 else 0.45 if days<=180 else 0.20
        if buy:
            bp+=rec
            if days<=90: buys90+=1
        elif sell:
            sp+=rec*0.35
            if days<=90: sells90+=1
    if bp==0 and sp==0: return None,0,0,latest
    return float(np.clip(50+(bp-sp)*18,15,100)),buys90,sells90,latest

def analyze_ticker(ticker, full=True):
    hist = get_history(ticker, "2y")
    if hist is None or hist.empty or "Close" not in hist.columns:
        return None

    close = hist["Close"].dropna()
    if len(close) < 220:
        return None

    current = float(close.iloc[-1])
    try:
        last_price_date = pd.Timestamp(close.index[-1]).strftime("%d.%m.%Y")
    except Exception:
        last_price_date = str(close.index[-1])

    def calendar_return(days):
        try:
            idx = pd.DatetimeIndex(close.index)
            last_dt = pd.Timestamp(idx[-1])
            target = last_dt - pd.Timedelta(days=days)
            pos = idx.searchsorted(target, side="right") - 1
            if pos < 0:
                return np.nan
            old_price = float(close.iloc[pos])
            return (current / old_price - 1) * 100 if old_price > 0 else np.nan
        except Exception:
            return np.nan

    ret_30d = calendar_return(30)
    ret_90d = calendar_return(90)
    ret_1y = calendar_return(365)
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
    insider_tx = get_insider_data(ticker) if full else None
    insider_source = "Ingen sikre data"
    if insider_tx is not None and len(insider_tx):
        if "Source" in insider_tx.columns and insider_tx["Source"].notna().any():
            insider_source = str(insider_tx["Source"].dropna().iloc[0])
        else:
            insider_source = "Yahoo/yfinance"
    insider_score, insider_buys90, insider_sells90, insider_latest = score_insider_activity(insider_tx)
    name = info.get("shortName") or info.get("longName") or dict(TOP50).get(ticker, ticker)
    currency = info.get("currency") or "NOK"
    website = info.get("website")
    sector = info.get("sector")
    industry = info.get("industry")
    business_summary = info.get("longBusinessSummary")
    yahoo_url = f"https://finance.yahoo.com/quote/{ticker}"

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
    # Utbytte: beregn helst fra årlig utbytte per aksje / kurs.
    # Dette unngår at Yahoo/yfinance sine prosentformater tolkes 100x feil.
    dividend_rate = safe_num(info.get("dividendRate"))
    current_price_info = safe_num(info.get("currentPrice")) or current
    if dividend_rate is not None and current_price_info and current_price_info > 0:
        dividend_yield = (dividend_rate / current_price_info) * 100
    else:
        # Fallback: nyere yfinance gir normalt dividendYield direkte i prosent,
        # f.eks. 5.61 for 5.61 %, ikke 0.0561.
        dividend_yield = safe_num(info.get("dividendYield"))
        if dividend_yield is not None and dividend_yield > 100:
            dividend_yield = None

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

    # Fundamental score = hovedsakelig verdsettelse.
    # Vi unngår å telle ROE/marginer to ganger ved å flytte dem til kvalitet.
    fund_parts = []
    if pe is not None and pe > 0:
        fund_parts.append(95 if pe < 12 else 80 if pe < 18 else 65 if pe < 25 else 45 if pe < 35 else 25)
    if fwd_pe is not None and fwd_pe > 0:
        fund_parts.append(95 if fwd_pe < 12 else 80 if fwd_pe < 18 else 65 if fwd_pe < 25 else 45 if fwd_pe < 35 else 25)
    if pb is not None and pb > 0:
        fund_parts.append(90 if pb < 1.5 else 70 if pb < 3 else 50 if pb < 5 else 30)
    if ev_ebitda is not None and ev_ebitda > 0:
        fund_parts.append(90 if ev_ebitda < 8 else 70 if ev_ebitda < 12 else 50 if ev_ebitda < 18 else 30)
    fundamental = avg_or_nan(fund_parts)

    # Risiko: høy score betyr lavere/mer håndterbar risiko.
    risk_parts = [
        90 if vol < 20 else 75 if vol < 30 else 55 if vol < 40 else 30,
        90 if mdd > -20 else 70 if mdd > -35 else 50 if mdd > -50 else 25,
    ]
    if beta is not None:
        risk_parts.append(90 if beta < 0.8 else 70 if beta < 1.2 else 50 if beta < 1.6 else 30)
    if debt_to_equity is not None:
        risk_parts.append(90 if debt_to_equity < 50 else 70 if debt_to_equity < 100 else 50 if debt_to_equity < 200 else 30)
    risk = avg_or_nan(risk_parts)

    # Kvalitet og vekst.
    quality_parts = []
    if roe is not None:
        quality_parts.append(95 if roe > 20 else 75 if roe > 12 else 55 if roe > 5 else 30)
    if op_margin is not None:
        quality_parts.append(90 if op_margin > 20 else 70 if op_margin > 10 else 55 if op_margin > 5 else 35)
    if revenue_growth is not None:
        quality_parts.append(90 if revenue_growth > 15 else 75 if revenue_growth > 5 else 55 if revenue_growth > 0 else 30)
    if earnings_growth is not None:
        quality_parts.append(90 if earnings_growth > 15 else 75 if earnings_growth > 5 else 55 if earnings_growth > 0 else 30)
    if current_ratio is not None:
        quality_parts.append(85 if current_ratio > 1.5 else 65 if current_ratio > 1.0 else 40)
    quality = avg_or_nan(quality_parts)

    # Utbytte-score.
    # Høyt utbytte belønnes, men ekstremt høy direkteavkastning får lavere score
    # fordi det ofte kan være et faresignal eller skyldes et ekstraordinært utbytte.
    dividend_score = np.nan
    if dividend_yield is not None and np.isfinite(dividend_yield):
        if dividend_yield <= 0:
            dividend_score = 20
        elif dividend_yield < 2:
            dividend_score = 35
        elif dividend_yield < 4:
            dividend_score = 55
        elif dividend_yield < 6:
            dividend_score = 75
        elif dividend_yield < 9:
            dividend_score = 90
        elif dividend_yield < 12:
            dividend_score = 95
        elif dividend_yield < 15:
            dividend_score = 75
        else:
            dividend_score = 45

    # Ny totalvekt:
    # Teknisk 30 %, Fundamental 25 %, Kvalitet 20 %, Risiko 15 %, Utbytte 10 %.
    # Manglende kategorier utelates og de resterende vektene normaliseres.
    parts, weights = [tech], [0.30]
    if np.isfinite(fundamental):
        parts.append(fundamental); weights.append(0.25)
    if np.isfinite(quality):
        parts.append(quality); weights.append(0.20)
    if np.isfinite(risk):
        parts.append(risk); weights.append(0.15)
    if np.isfinite(dividend_score):
        parts.append(dividend_score); weights.append(0.10)
    total = round(float(np.average(parts, weights=weights)), 1)
    if insider_score is not None:
        total = round(total * 0.93 + insider_score * 0.07, 1)

    fair_value = current * 18 / pe if pe is not None and pe > 0 else None

    def trend_label(v):
        if v is None or not np.isfinite(v):
            return "N/A"
        if v > 2:
            return "↗ Opp"
        if v < -2:
            return "↘ Ned"
        return "→ Sideveis"

    return {
        "Markedsverdi-rang": MARKET_CAP_RANK.get(ticker), "Ticker": ticker, "Selskap": name, "Valuta": currency, "Kurs": current,
        "Siste kursdato": last_price_date, "Nettside": website, "Yahoo URL": yahoo_url,
        "Sektor": sector, "Bransje": industry, "Beskrivelse": business_summary,
        "Score": total,
        "Innside-score": insider_score,
        "Innside 90d": f"+{insider_buys90}/-{insider_sells90}" if insider_score is not None else "Ingen sikre data",
        "Innside-kilde": insider_source if insider_score is not None else "Ingen sikre data",
        "Siste innsidehandel": insider_latest.strftime("%d.%m.%Y") if insider_latest is not None else "–",
        "Teknisk": tech, "Fundamental": fundamental, "Risiko": risk, "Kvalitet": quality,
        "30 dager %": ret_30d, "90 dager %": ret_90d, "1 år %": ret_1y,
        "Trend 30d": trend_label(ret_30d), "Trend 90d": trend_label(ret_90d), "Trend 1 år": trend_label(ret_1y),
        "6 mnd %": ret_6m, "3 mnd %": ret_3m,
        "Volatilitet %": vol, "Sharpe": sharpe, "Maks drawdown %": mdd,
        "RSI14": rsi14, "MACD": macd_line, "MACD signal": macd_signal, "MACD hist": macd_hist,
        "Fra 52u topp %": from_high, "MA50": ma50, "MA200": ma200,
        "P/E": pe, "Forward P/E": fwd_pe, "P/B": pb, "EV/EBITDA": ev_ebitda,
        "ROE %": roe, "ROA %": roa, "Profit margin %": profit_margin,
        "Operating margin %": op_margin, "Revenue growth %": revenue_growth,
        "Earnings growth %": earnings_growth, "Debt/Equity": debt_to_equity,
        "Current ratio": current_ratio, "Beta": beta, "Dividend yield %": dividend_yield, "Utbytte-score": dividend_score,
        "Fair value proxy": fair_value, "_history": hist, "_reasons": reasons,
    }

# Persist selected ticker across tabs.
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "EQNR.OL"
if "top50_results" not in st.session_state:
    st.session_state.top50_results = None
if "top50_mode" not in st.session_state:
    st.session_state.top50_mode = None
if "top50_market" not in st.session_state:
    st.session_state.top50_market = None

with st.expander("ℹ️ Slik beregnes scoren"):
    st.markdown("""
**Totalscore 0–100** kombinerer flere faktorer. Høy score betyr at aksjen kommer godt ut på flere kriterier samtidig – ikke at den har en bestemt sannsynlighet for kursoppgang.

| Kriterium | Normal vekt | Hva vurderes |
|---|---:|---|
| 📈 Teknisk | 30 % | Kursutvikling, glidende snitt, momentum, RSI og MACD |
| 💰 Verdsettelse | 25 % | P/E, Forward P/E, P/B og EV/EBITDA |
| ⭐ Kvalitet og vekst | 20 % | ROE, driftsmargin, omsetningsvekst, resultatvekst og likviditet |
| 🛡️ Risiko | 15 % | Volatilitet, maksimalt kursfall, beta og gjeld |
| 💵 Utbytte | 10 % | Direkteavkastning; ekstremt høy yield får ikke automatisk toppscore |

**👤 Innsidehandel:** Når brukbare strukturerte data finnes, blandes innside-score inn med **7 %** av den ellers beregnede totalscoren. Nylige identifiserbare kjøp teller positivt og sterkere enn salg teller negativt. Manglende innside-data gir ingen straff.

**Tolkning:** 85–100 svært sterk · 75–84 sterk · 65–74 positiv · 55–64 nøytral/positiv · 45–54 nøytral · under 45 svak.

30 dager, 90 dager og 1 år i resultattabellen er faktisk kursutvikling og ikke egne ekstra poengsummer.

**Viktig:** Samme modell brukes på tvers av markedene. Banker, teknologi, energi, shipping og andre sektorer kan ha svært forskjellige normale nøkkeltall, så scoren bør brukes sammen med detaljanalysen.
""")

tab1, tab2, tab3 = st.tabs(["🔬 Enkeltanalyse", "🏆 Top 50", "📋 Tickerliste"])

with tab1:
    st.markdown("### Velg fra Top 50")
    selected_from_list = st.selectbox(
        "Velg aksje",
        options=TOP50_TICKERS,
        index=TOP50_TICKERS.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in TOP50_TICKERS else 0,
        format_func=lambda x: TOP50_LABELS[x],
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
            st.caption(f"Siste tilgjengelige kursdato: **{r['Siste kursdato']}**")
            c, d = st.columns(2)
            c.metric("30 dager", fmt(r["30 dager %"], "%"))
            d.metric("90 dager", fmt(r["90 dager %"], "%"))
            e, f = st.columns(2)
            e.metric("1 år", fmt(r["1 år %"], "%"))
            f.metric("RSI", fmt(r["RSI14"]))
            st.caption(
                f"Trend: 30d **{r['Trend 30d']}** · 90d **{r['Trend 90d']}** · 1 år **{r['Trend 1 år']}**"
            )
            st.progress(min(max(r["Score"] / 100, 0), 1))

            st.markdown("### Delscorer")
            st.dataframe(pd.DataFrame({
                "Område": ["Teknisk", "Fundamental", "Kvalitet", "Risiko", "Utbytte"],
                "Score": [r["Teknisk"], r["Fundamental"], r["Kvalitet"], r["Risiko"], r["Utbytte-score"]],
            }), hide_index=True, use_container_width=True)

            chart = r["_history"][["Close"]].copy()
            chart["MA50"] = chart["Close"].rolling(50).mean()
            chart["MA200"] = chart["Close"].rolling(200).mean()
            st.line_chart(chart, use_container_width=True)

            st.markdown("### 👤 Innsidehandel")
            if r["Innside-score"] is None:
                st.warning(
                    "Ingen sikre automatiske innsidehandler funnet. Dette betyr ikke nødvendigvis at det ikke finnes "
                    "primærinnsidehandler. Kontroller Euronext/Oslo Børs. Manglende data påvirker ikke totalscoren."
                )
                i1, i2 = st.columns(2)
                i1.metric("Innside-score", "–")
                i2.metric("Innside 90d", "Ingen sikre data")
            else:
                i1, i2, i3 = st.columns(3)
                i1.metric("Innside-score", f'{r["Innside-score"]:.0f}/100')
                i2.metric("Kjøp/salg 90d", r["Innside 90d"])
                i3.metric("Siste handel", r["Siste innsidehandel"])
                st.caption("Kilde vises i resultatet. For Oslo forsøkes Euronext Oslo Børs først; Yahoo/yfinance brukes som reserve. Innside teller 7 % når sikre data finnes.")
            st.link_button(
                "🏛️ Kontroller primærinnsidehandel hos Euronext",
                "https://live.euronext.com/nb/markets/oslo/equities/company-news",
                use_container_width=True,
            )

            st.markdown("### Om selskapet")
            info_rows = []
            if r.get("Sektor"):
                info_rows.append(["Sektor", r["Sektor"]])
            if r.get("Bransje"):
                info_rows.append(["Bransje", r["Bransje"]])
            if info_rows:
                st.dataframe(
                    pd.DataFrame(info_rows, columns=["Felt", "Info"]),
                    hide_index=True,
                    use_container_width=True
                )

            link_cols = st.columns(2)
            if r.get("Nettside"):
                link_cols[0].link_button("🌐 Selskapets nettside", r["Nettside"], use_container_width=True)
            link_cols[1].link_button("📈 Yahoo Finance", r["Yahoo URL"], use_container_width=True)

            if r.get("Beskrivelse"):
                with st.expander("Les mer om selskapet"):
                    st.write(r["Beskrivelse"])

            st.markdown("### Teknisk")
            st.dataframe(pd.DataFrame([
                ["30 dager", fmt(r["30 dager %"], "%")],
                ["90 dager", fmt(r["90 dager %"], "%")],
                ["1 år", fmt(r["1 år %"], "%")],
                ["3 mnd (ca. 63 børsdager)", fmt(r["3 mnd %"], "%")],
                ["6 mnd", fmt(r["6 mnd %"], "%")],
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
    st.markdown(f"### Analyser {N_STOCKS} aksjer · {MARKET_NAME}")
    mode = st.radio(
        "Analysemodus",
        ["Full analyse", "Hurtigmodus"],
        horizontal=True,
        help="Full analyse henter flere fundamentale nøkkeltall. Hurtigmodus er raskere og fokuserer mest på kurs/teknisk data.",
    )
    min_score = st.slider("Vis bare score over", 0, 90, 0, step=5)
    sort_by = st.selectbox("Sorter etter", ["Score", "Innside-score", "Kurs", "30 dager %", "90 dager %", "1 år %", "Direkteavkastning %", "Utbytte-score", "Teknisk", "Fundamental", "Kvalitet", "Risiko"])

    if st.button(f"Analyser {MARKET_NAME} ({N_STOCKS} aksjer)", type="primary", use_container_width=True):
        results = []
        progress = st.progress(0)
        status = st.empty()
        full = mode == "Full analyse"

        for i, ticker40 in enumerate(TOP50_TICKERS):
            status.write(f"Analyserer {TOP50_LABELS[ticker40]} ({i+1}/{N_STOCKS})...")
            r = analyze_ticker(ticker40, full=full)
            if r:
                results.append(r)
            progress.progress((i + 1) / N_STOCKS)

        status.empty()
        st.session_state.top50_results = results
        st.session_state.top50_mode = mode
        st.session_state.top50_market = selected_market

    # Behold resultatene i session_state slik at valg av selskap,
    # lenker og andre widgets ikke nullstiller analysen ved Streamlit-rerun.
    results = st.session_state.top50_results
    if st.session_state.top50_market != selected_market:
        results = None

    if results is not None:
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
                "Vurdering", "Score", "Markedsverdi-rang", "Ticker", "Selskap",
                "Kurs", "Siste kursdato", "30 dager %", "90 dager %", "1 år %",
                "Teknisk", "Fundamental", "Kvalitet", "Risiko", "Utbytte-score",
                "Volatilitet %", "Direkteavkastning %", "P/E", "ROE %",
                "Innside-score", "Innside 90d", "Innside-kilde"
            ]
            display = df[show_cols].copy()
            for col in ["Kurs", "30 dager %", "90 dager %", "1 år %", "Score", "Innside-score", "Teknisk", "Fundamental",
                        "Kvalitet", "Risiko", "Utbytte-score", "Volatilitet %", "Direkteavkastning %", "P/E", "ROE %"]:
                display[col] = pd.to_numeric(display[col], errors="coerce").round(1)

            mode_txt = st.session_state.top50_mode or mode
            st.success(f"Analyserte {len(results)} av {N_STOCKS} aksjer · {MARKET_NAME} · {mode_txt}.")

            st.markdown("### Resultater")
            st.caption("Vurdering og Score står først. Innsidekolonnene ligger helt til slutt. «Ingen sikre data» betyr at innside ikke påvirker totalscoren.")
            st.caption("Sveip sidelengs i tabellen for å se alle kolonnene.")
            table_height = min(38 * (len(display) + 1) + 6, 1900)
            st.dataframe(
                display,
                use_container_width=True,
                height=table_height,
            )

            st.markdown("### Topp 10")
            for rank, (_, row) in enumerate(df.head(10).iterrows(), start=1):
                div_txt = fmt(row["Direkteavkastning %"], "%")
                st.write(
                    f"**{rank}. {row['Ticker']} — {row['Score']:.0f}/100** · {row['Selskap']} · "
                    f"Kurs {row['Kurs']:.2f} · 30d {fmt(row['30 dager %'], '%')} · "
                    f"90d {fmt(row['90 dager %'], '%')} · 1 år {fmt(row['1 år %'], '%')} · Utbytte {div_txt}"
                )

            st.markdown("### Send ticker til enkeltanalyse")
            if len(df):
                pick = st.selectbox(
                    "Velg en aksje fra resultatlisten",
                    df["Ticker"].tolist(),
                    format_func=lambda x: f"{x} — {df.loc[df['Ticker'] == x, 'Selskap'].iloc[0]}",
                    key="result_pick",
                )

                picked_row = df.loc[df["Ticker"] == pick].iloc[0]
                st.caption(f"Siste tilgjengelige kursdato: {picked_row['Siste kursdato']}")

                link_cols2 = st.columns(2)
                if pd.notna(picked_row.get("Nettside")) and picked_row.get("Nettside"):
                    link_cols2[0].link_button(
                        "🌐 Selskapets nettside",
                        picked_row["Nettside"],
                        use_container_width=True
                    )
                link_cols2[1].link_button(
                    "📈 Yahoo Finance",
                    picked_row["Yahoo URL"],
                    use_container_width=True
                )

                if st.button("Bruk denne i enkeltanalyse", use_container_width=True):
                    st.session_state.selected_ticker = pick
                    st.success(f"{pick} er valgt. Åpne fanen Enkeltanalyse.")

            csv = display.to_csv(index=True).encode("utf-8")
            st.download_button(
                "Last ned Top 50-resultat som CSV",
                data=csv,
                file_name=f"{MARKET_NAME.lower().replace(' ', '_')}_analyse.csv",
                mime="text/csv",
                use_container_width=True,
            )

            if st.button("🗑️ Nullstill Top 50-analyse", use_container_width=True):
                st.session_state.top50_results = None
                st.session_state.top50_mode = None
                st.session_state.top50_market = None
                st.rerun()

with tab3:
    st.markdown(f"### Tickerliste · {MARKET_NAME}")
    st.write("Trykk og hold på en ticker på iPhone for å kopiere den, eller velg den direkte i Enkeltanalyse.")
    ticker_df = pd.DataFrame([(i, t, n) for i, (t, n) in enumerate(TOP50, start=1)], columns=["Nr.", "Ticker", "Selskap"])
    st.dataframe(ticker_df, hide_index=True, use_container_width=True)

    st.markdown("### Kopierbar liste")
    st.code("\n".join(TOP50_TICKERS), language=None)

st.markdown("---")
st.caption(
    f"Aksjelisten for {MARKET_NAME} er en kuratert screeningliste og ikke en garantert sanntidsrangering etter markedsverdi. "
    "Sammensetning og rangering kan endre seg. Scoren er mekanisk og kan ikke forutsi fremtidig avkastning."
)
st.markdown(
    """<div style="text-align:center;margin-top:2.5rem;padding:1rem 0;font-size:0.8rem;opacity:0.65;border-top:1px solid rgba(128,128,128,0.25);">© GS, Skjetten 2026 · Smart Aksjeanalyse V6.4</div>""",
    unsafe_allow_html=True,
)
