import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import urllib.request
import urllib.parse
import html as html_lib
import re

def format_price_time(ts):
    if ts is None or pd.isna(ts):
        return "Ukjent", "Ukjent"
    try:
        t = pd.Timestamp(ts)
        label = t.strftime("%d.%m.%Y %H:%M")
        if t.tzinfo is not None:
            now = pd.Timestamp.now(tz=t.tz)
            mins = max(0, int((now - t).total_seconds() // 60))
            age = f"{mins} min" if mins < 60 else (f"{mins//60} t {mins%60} min" if mins < 1440 else f"{mins//1440} d")
        else:
            age = "Ukjent"
        return label, age
    except Exception:
        return str(ts), "Ukjent"

st.set_page_config(
    page_title="Smart Aksjeanalyse",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container {
    max-width: 96vw !important;
    padding-left: 1.2rem !important;
    padding-right: 1.2rem !important;
}
[data-testid="stDataFrame"], [data-testid="stDataFrame"] * {
    font-size: 0.78rem !important;
}
@media (min-width: 900px) {
    .stMarkdown p, label { font-size: 0.88rem; }
    h1 { font-size: 1.8rem !important; }
    h2 { font-size: 1.45rem !important; }
    h3 { font-size: 1.2rem !important; }
}
@media (max-width: 899px) {
    .block-container {
        max-width: 100% !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }
    [data-testid="stDataFrame"], [data-testid="stDataFrame"] * {
        font-size: 0.82rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    [data-testid="stToolbar"] {display:none !important;}
    [data-testid="stDecoration"] {display:none !important;}
    #MainMenu {visibility:hidden !important;}
    footer {visibility:hidden !important;}
    header {visibility:hidden !important;}
    .block-container {padding-top:0.5rem !important; padding-bottom:2rem !important; max-width:96vw !important;}
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

MARKET_SCREEN = {
    "🇳🇴 Oslo Børs": {"region": "no", "exchanges": ["OSL"]},
    "🇸🇪 Stockholm": {"region": "se", "exchanges": ["STO"]},
    "🇩🇰 København": {"region": "dk", "exchanges": ["CPH"]},
    "🇫🇮 Helsinki": {"region": "fi", "exchanges": ["HEL"]},
    "🇺🇸 USA": {"region": "us", "exchanges": ["NYQ", "NMS", "NGM"]},
}

@st.cache_data(ttl=21600, show_spinner=False)
def get_top_market_stocks(market_key, limit=100):
    """Hent de største aksjene etter Yahoo intraday market cap.
    Faller tilbake til den kuraterte listen hvis Yahoo-screeneren ikke svarer.
    """
    fallback = MARKETS[market_key]
    cfg = MARKET_SCREEN[market_key]
    try:
        q = yf.EquityQuery("and", [
            yf.EquityQuery("eq", ["region", cfg["region"]]),
            yf.EquityQuery("is-in", ["exchange", *cfg["exchanges"]]),
            yf.EquityQuery("gt", ["intradaymarketcap", 0]),
        ])
        response = yf.screen(
            q,
            size=limit,
            sortField="intradaymarketcap",
            sortAsc=False,
        )
        quotes = response.get("quotes", []) if isinstance(response, dict) else []
        rows = []
        seen = set()
        for quote in quotes:
            ticker = quote.get("symbol")
            if not ticker or ticker in seen:
                continue
            name = quote.get("shortName") or quote.get("longName") or ticker
            rows.append((ticker, name))
            seen.add(ticker)
            if len(rows) >= limit:
                break
        if len(rows) >= 50:
            return rows, "Yahoo Finance markedsverdi"
    except Exception:
        pass
    return fallback[:limit], "Kuratert reserveliste"

selected_market = st.selectbox("🌍 Velg børs / marked", list(MARKETS.keys()), key="selected_market")
TOP50, universe_source = get_top_market_stocks(selected_market, 100)
TOP50_TICKERS = [t for t, _ in TOP50]
TOP50_LABELS = {t: f"{t} — {name}" for t, name in TOP50}
MARKET_CAP_RANK = {t: i for i, (t, _) in enumerate(TOP50, start=1)}
MARKET_NAME = selected_market.split(" ", 1)[1]
N_STOCKS = len(TOP50)

@st.cache_data(ttl=900, show_spinner=False)
def get_history(ticker, period="2y"):
    try:
        return yf.Ticker(ticker).history(period=period, auto_adjust=False)
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

    # Start alltid med siste sikre datapunkt fra historikken.
    current = float(close.iloc[-1])
    latest_price_time = close.index[-1]
    try:
        last_price_date = pd.Timestamp(latest_price_time).strftime("%d.%m.%Y")
    except Exception:
        last_price_date = str(latest_price_time)
    latest_time_label, latest_age = format_price_time(latest_price_time)

    # Forsøk deretter å hente et ferskere 5-minutters datapunkt fra Yahoo.
    # Hvis dette feiler, beholdes historikkverdiene over.
    try:
        intraday = yf.Ticker(ticker).history(
            period="1d",
            interval="5m",
            auto_adjust=False,
            prepost=False,
        )
        if intraday is not None and not intraday.empty and "Close" in intraday.columns:
            intraday_close = intraday["Close"].dropna()
            if not intraday_close.empty:
                candidate_time = intraday_close.index[-1]
                # Ikke erstatt siste dagskurs med en eldre intradagkurs.
                if pd.Timestamp(candidate_time).date() >= pd.Timestamp(latest_price_time).date():
                    current = float(intraday_close.iloc[-1])
                    latest_price_time = candidate_time
                    last_price_date = pd.Timestamp(latest_price_time).strftime("%d.%m.%Y")
                    latest_time_label, latest_age = format_price_time(latest_price_time)
    except Exception:
        pass

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
    # Innsideanalyse er midlertidig deaktivert i V6.5.
    insider_tx = None
    insider_source = None
    insider_score, insider_buys90, insider_sells90, insider_latest = None, 0, 0, None
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
        "Siste kursdato": last_price_date,
        "Siste kurstid": pd.Timestamp(latest_price_time).strftime("%d.%m %H:%M") if latest_price_time is not None else "–",
        "Siste kurstid full": latest_time_label,
        "Kursalder": latest_age,
        "Kurskilde": "Yahoo Finance / yfinance",
        "Nettside": website, "Yahoo URL": yahoo_url,
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


**Tolkning:** 85–100 svært sterk · 75–84 sterk · 65–74 positiv · 55–64 nøytral/positiv · 45–54 nøytral · under 45 svak.

30 dager, 90 dager og 1 år viser ren kursendring fra ujusterte Yahoo-sluttkurser, uten utbytte. Periodene er kalenderdager med nærmeste tidligere handelsdag som sammenligningspunkt. Siste kurs kan være intradag og Yahoo-data kan være forsinket.

**Viktig:** Samme modell brukes på tvers av markedene. Banker, teknologi, energi, shipping og andre sektorer kan ha svært forskjellige normale nøkkeltall, så scoren bør brukes sammen med detaljanalysen.
""")

tab1, tab2, tab3 = st.tabs(["🔬 Enkeltanalyse", "🏆 Top 100", "📋 Tickerliste"])

with tab1:
    st.markdown("### Velg fra Top 100")
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

    if "single_analysis_result" not in st.session_state:
        st.session_state.single_analysis_result = None
    if st.button("Kjør avansert analyse", type="primary", use_container_width=True):
        st.session_state.selected_ticker = ticker
        with st.spinner(f"Analyserer {ticker}..."):
            st.session_state.single_analysis_result = analyze_ticker(ticker, full=True)

    r = st.session_state.single_analysis_result
    if r is None:
        st.info("Velg en aksje og trykk «Kjør avansert analyse» for å vise kursgraf og nøkkeltall.")
    else:
        st.subheader(f"{r['Selskap']} ({r['Ticker']})")
        a, b = st.columns(2)
        a.metric("Kurs", f"{r['Kurs']:.2f} {r['Valuta']}")
        b.metric("Total score", f"{r['Score']:.0f}/100")
        st.caption(
            f"Siste tilgjengelige kurs: **{r.get('Siste kurstid full', r['Siste kursdato'])}** · "
            f"Kursalder: **{r.get('Kursalder', 'Ukjent')}** · Kilde: Yahoo Finance / yfinance. "
            "Data kan være forsinket."
        )
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

        st.markdown("### 📈 Historisk aksjekurs")
        chart_period = st.radio("Velg periode", ["1 år", "2 år", "5 år"], horizontal=True, key="single_chart_period")
        period_code = {"1 år": "1y", "2 år": "2y", "5 år": "5y"}[chart_period]
        history_chart = get_history(r["Ticker"], period=period_code)
        if history_chart is not None and not history_chart.empty and "Close" in history_chart.columns:
            chart = history_chart[["Close"]].dropna().copy()
            chart.index = pd.to_datetime(chart.index)
            chart.index.name = "Dato"
            chart = chart.rename(columns={"Close": "Kurs"})
            st.line_chart(chart, use_container_width=True, x_label="Dato", y_label=f"Kurs ({r['Valuta']})")
            st.caption("Historisk sluttkurs uten utbyttejustering. Kilde: Yahoo Finance. Kursdata kan være forsinket.")
        else:
            st.warning("Fant ingen kurshistorikk for valgt periode.")

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
    st.caption(f"Univers: {universe_source}. Målet er de 100 største etter markedsverdi når Yahoo-screeneren er tilgjengelig.")
    mode = st.radio(
        "Analysemodus",
        ["Full analyse", "Hurtigmodus"],
        horizontal=True,
        help="Full analyse henter flere fundamentale nøkkeltall. Hurtigmodus er raskere og fokuserer mest på kurs/teknisk data.",
    )
    min_score = st.slider("Vis bare score over", 0, 90, 0, step=5)
    sort_by = st.selectbox("Sorter etter", ["Score", "Kurs", "30 dager %", "90 dager %", "1 år %", "Direkteavkastning %", "Utbytte-score", "Teknisk", "Fundamental", "Kvalitet", "Risiko"])

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

            company_search = st.text_input(
                "🔎 Søk i Top 100",
                placeholder="Skriv ticker eller selskapsnavn, f.eks. EQNR eller Equinor",
                key=f"top100_search_{selected_market}",
            ).strip()
            if company_search:
                search_lower = company_search.lower()
                df = df[
                    df["Ticker"].astype(str).str.lower().str.contains(search_lower, regex=False)
                    | df["Selskap"].astype(str).str.lower().str.contains(search_lower, regex=False)
                ]

            if min_score > 0:
                df = df[df["Score"] >= min_score]

            if sort_by in df.columns:
                df = df.sort_values(sort_by, ascending=False, na_position="last")

            df = df.reset_index(drop=True)
            df.index = df.index + 1

            show_cols = [
                "Vurdering", "Score", "Ticker", "Selskap", "Kurs", "Siste kurstid",
                "30 dager %", "90 dager %", "1 år %",
                "Teknisk", "Fundamental", "Kvalitet", "Risiko"
            ]
            display = df[show_cols].copy()
            for col in ["Kurs", "30 dager %", "90 dager %", "1 år %", "Score", "Teknisk", "Fundamental",
                        "Kvalitet", "Risiko", "Utbytte-score", "Volatilitet %", "Direkteavkastning %", "P/E", "ROE %"]:
                if col in display.columns:
                    display[col] = pd.to_numeric(display[col], errors="coerce").round(1)

            mode_txt = st.session_state.top50_mode or mode
            st.success(f"Analyserte {len(results)} av {N_STOCKS} aksjer · {MARKET_NAME} · {mode_txt}.")

            st.markdown("### Resultater")
            if company_search:
                st.caption(f"Søket «{company_search}» ga {len(df)} treff i analyserte aksjer.")
            st.caption("Hovedtabellen viser alle 13 kolonnene med kompakte overskrifter. Klikk på en rad i tabellen for å vise kursgraf og detaljer under.")
            st.caption("Sist kurs viser dato og klokkeslett (dag.måned time:minutt). Full dato og delscorer vises under tabellen.")
            table_event = st.dataframe(
                display,
                on_select="rerun",
                selection_mode="single-row",
                key="top100_clickable_table",
                use_container_width=True,
                height=720,
                hide_index=True,
                column_config={
                    "Vurdering": st.column_config.TextColumn("Vurd.", width=66),
                    "Score": st.column_config.NumberColumn("Score", format="%.0f", width=54),
                    "Ticker": st.column_config.TextColumn("Ticker", width=88),
                    "Selskap": st.column_config.TextColumn("Selskap", width=210),
                    "Kurs": st.column_config.NumberColumn("Kurs", format="%.2f", width=72),
                    "Siste kurstid": st.column_config.TextColumn("Sist kurs", width=100),
                    "30 dager %": st.column_config.NumberColumn("30d %", format="%.1f%%", width=62),
                    "90 dager %": st.column_config.NumberColumn("90d %", format="%.1f%%", width=62),
                    "1 år %": st.column_config.NumberColumn("1år %", format="%.1f%%", width=62),
                    "Teknisk": st.column_config.NumberColumn("Tekn.", format="%.0f", width=58),
                    "Fundamental": st.column_config.NumberColumn("Fund.", format="%.0f", width=58),
                    "Kvalitet": st.column_config.NumberColumn("Kval.", format="%.0f", width=58),
                    "Risiko": st.column_config.NumberColumn("Ris.", format="%.0f", width=58),
                },
            )

            st.markdown("### 🔎 Detaljer for valgt aksje")
            detail_options = df["Ticker"].tolist()
            selected_rows = table_event.selection.rows if table_event is not None else []
            if selected_rows and 0 <= selected_rows[0] < len(detail_options):
                st.session_state["top100_clicked_ticker"] = detail_options[selected_rows[0]]
            clicked = st.session_state.get("top100_clicked_ticker")
            if clicked not in detail_options:
                clicked = detail_options[0] if detail_options else None
            if clicked is None:
                st.info("Ingen aksjer samsvarer med søket.")
                st.stop()
            detail_ticker = st.selectbox(
                "Valgt aksje – klikk gjerne på en annen rad i tabellen",
                detail_options,
                index=detail_options.index(clicked),
                format_func=lambda t: f"{t} — {TOP50_LABELS.get(t, t).split(' — ', 1)[-1]}",
                key="top50_detail_ticker",
            )
            st.session_state["top100_clicked_ticker"] = detail_ticker
            detail_row = df.loc[df["Ticker"] == detail_ticker].iloc[0]

            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Score", f"{detail_row.get('Score', 0):.0f}/100")
            d2.metric("Kurs", f"{detail_row.get('Kurs', 0):.2f}")
            pe_val = detail_row.get("P/E")
            d3.metric("P/E", "N/A" if pd.isna(pe_val) else f"{pe_val:.1f}")
            yield_val = detail_row.get("Direkteavkastning %")
            d4.metric("Utbytte", "N/A" if pd.isna(yield_val) else f"{yield_val:.1f}%")

            e1, e2, e3, e4 = st.columns(4)
            roe_val = detail_row.get("ROE %")
            vol_val = detail_row.get("Volatilitet %")
            e1.metric("ROE", "N/A" if pd.isna(roe_val) else f"{roe_val:.1f}%")
            e2.metric("Volatilitet", "N/A" if pd.isna(vol_val) else f"{vol_val:.1f}%")
            e3.metric("30 dager", f"{detail_row.get('30 dager %', 0):.1f}%")
            e4.metric("1 år", f"{detail_row.get('1 år %', 0):.1f}%")

            st.info(
                f"🕒 Siste tilgjengelige kurs: {detail_row.get('Siste kurstid full', 'Ukjent')} · "
                f"Kursalder: {detail_row.get('Kursalder', 'Ukjent')} · "
                f"Kilde: {detail_row.get('Kurskilde', 'Yahoo Finance / yfinance')}. "
                "Yahoo-data kan være forsinket og er ikke garantert sanntid."
            )

            st.caption(
                f"Vurdering: {detail_row.get('Vurdering', 'N/A')} · "
                f"Teknisk {detail_row.get('Teknisk', 'N/A')} · "
                f"Fundamental {detail_row.get('Fundamental', 'N/A')} · "
                f"Kvalitet {detail_row.get('Kvalitet', 'N/A')} · "
                f"Risiko {detail_row.get('Risiko', 'N/A')} · "
                f"Utbytte-score {detail_row.get('Utbytte-score', 'N/A')}"
            )

            st.markdown("### 📈 Kursutvikling for valgt aksje")
            period_detail = st.radio(
                "Vis historisk kurs", ["1 år", "3 år", "5 år"],
                horizontal=True, key="top100_chart_period",
            )
            period_lookup = {"1 år": "1y", "3 år": "3y", "5 år": "5y"}
            detail_hist = get_history(detail_ticker, period_lookup[period_detail])
            if detail_hist is not None and not detail_hist.empty and "Close" in detail_hist.columns:
                price_chart = detail_hist[["Close"]].dropna().rename(columns={"Close": "Kurs"})
                price_chart.index = pd.to_datetime(price_chart.index)
                price_chart.index.name = "Dato"
                st.line_chart(price_chart, use_container_width=True, x_label="Dato", y_label="Kurs")
                first_price = float(price_chart["Kurs"].iloc[0])
                last_price = float(price_chart["Kurs"].iloc[-1])
                period_change = (last_price / first_price - 1) * 100 if first_price > 0 else None
                st.caption(
                    f"Endring i valgt periode: {period_change:+.1f} % · " if period_change is not None else ""
                )
                st.caption("Ujusterte historiske sluttkurser (uten utbytte). Kilde: Yahoo Finance. Kan være forsinket.")
            else:
                st.warning("Ingen historiske kursdata tilgjengelig for valgt periode.")

            st.markdown("### 📋 Flere nøkkeltall")
            extra_keys = [
                ("P/E", "P/E"), ("ROE %", "ROE"), ("Dividend yield %", "Direkteavkastning %"),
                ("Volatilitet %", "Volatilitet"), ("RSI14", "RSI 14"),
                ("MA50", "Glidende snitt 50 dager"), ("MA200", "Glidende snitt 200 dager"),
                ("Beta", "Beta"), ("Max drawdown %", "Største historiske fall"),
            ]
            extras = []
            for source_key, label in extra_keys:
                value = detail_row.get(source_key)
                if value is not None and not pd.isna(value):
                    extras.append({"Nøkkeltall": label, "Verdi": f"{value:.2f}" if isinstance(value, (int, float, np.number)) else str(value)})
            if extras:
                st.dataframe(pd.DataFrame(extras), hide_index=True, use_container_width=True)

            if st.button("🔬 Åpne full enkeltanalyse for valgt aksje", key="top100_open_full"):
                st.session_state.selected_ticker = detail_ticker
                with st.spinner(f"Henter selskapsinformasjon for {detail_ticker}..."):
                    st.session_state.single_analysis_result = analyze_ticker(detail_ticker, full=True)
                st.success("Full analyse er klar under fanen «Enkeltanalyse». Klikk på den fanen øverst.")

            st.markdown("### Topp 10")
            top10 = df.head(10)[["Ticker", "Selskap", "Score", "Vurdering", "Kurs", "30 dager %", "90 dager %", "1 år %"]].copy()
            st.dataframe(
                top10,
                use_container_width=True,
                hide_index=True,
                height=390,
                column_config={
                    "Score": st.column_config.NumberColumn("Score", format="%.0f"),
                    "Kurs": st.column_config.NumberColumn("Kurs", format="%.2f"),
                    "30 dager %": st.column_config.NumberColumn("30d %", format="%.1f%%"),
                    "90 dager %": st.column_config.NumberColumn("90d %", format="%.1f%%"),
                    "1 år %": st.column_config.NumberColumn("1 år %", format="%.1f%%"),
                },
            )

with tab3:
    st.markdown(f"### Top {N_STOCKS} tickerliste · {MARKET_NAME}")
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
    """<div style="text-align:center;margin-top:2.5rem;padding:1rem 0;font-size:0.8rem;opacity:0.65;border-top:1px solid rgba(128,128,128,0.25);">© GS, Skjetten 2026 · Smart Aksjeanalyse V7.8</div>""",
    unsafe_allow_html=True,
)
