import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="주식 투자 대시보드", layout="wide")
st.title("📈 주식 투자 대시보드")

RSI_PERIOD = 14
SIGNAL_PERIOD = 6

KOSPI_SCAN_LIST = {
    "삼성전자": "005930.KS",
    "삼성전자우": "005935.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성SDI": "006400.KS",
    "LG화학": "051910.KS",
    "포스코퓨처엠": "003670.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "현대모비스": "012330.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "KT": "030200.KS",
    "SK텔레콤": "017670.KS",
    "LG유플러스": "032640.KS",
    "KB금융": "105560.KS",
    "신한지주": "055550.KS",
    "하나금융지주": "086790.KS",
    "우리금융지주": "316140.KS",
    "한화에어로스페이스": "012450.KS",
    "HD한국조선해양": "009540.KS",
    "HD현대중공업": "329180.KS",
    "한화오션": "042660.KS",
    "POSCO홀딩스": "005490.KS",
    "고려아연": "010130.KS",
    "삼성바이오로직스": "207940.KS",
    "셀트리온": "068270.KS",
    "아모레퍼시픽": "090430.KS",
    "LG생활건강": "051900.KS",
    "한국전력": "015760.KS",
}

US_SCAN_LIST = {
    "NVDA": "NVDA",
    "MSFT": "MSFT",
    "AAPL": "AAPL",
    "AMZN": "AMZN",
    "GOOGL": "GOOGL",
    "META": "META",
    "TSLA": "TSLA",
    "PLTR": "PLTR",
    "AMD": "AMD",
    "AVGO": "AVGO",
    "SOXL": "SOXL",
    "QQQ": "QQQ",
    "SPY": "SPY",
}

SCAN_LIST = {}
SCAN_LIST.update(KOSPI_SCAN_LIST)
SCAN_LIST.update(US_SCAN_LIST)

WATCHLIST = {
    "삼성전자": "005930.KS",
    "삼성전자우": "005935.KS",
    "KT": "030200.KS",
    "SK하이닉스": "000660.KS",
    "NAVER": "035420.KS",
    "현대차": "005380.KS",
    "SOXL": "SOXL",
    "NVDA": "NVDA",
    "PLTR": "PLTR",
}


def calc_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def judge_signal(close, ma20, ma60, rsi, signal, volume, avg_volume):
    if rsi > signal and close > ma20 and ma20 > ma60 and volume > avg_volume:
        return "🟢 강매수"
    elif rsi > signal and close > ma20:
        return "🟡 매수관심"
    elif rsi < signal and close < ma20 and ma20 < ma60:
        return "⚫ 하락추세"
    elif rsi < signal and close < ma20:
        return "🔴 약세전환"
    else:
        return "🟠 관망"


def score_stock(close, ma20, ma60, rsi, signal, volume, avg_volume, recent_buy):
    score = 0
    if close > ma20:
        score += 20
    if ma20 > ma60:
        score += 20
    if rsi > signal:
        score += 20
    if volume > avg_volume:
        score += 20
    if recent_buy:
        score += 20
    return score


def analyze_df(df):
    close = df["Close"]
    volume = df["Volume"]

    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()
    avg_volume = volume.rolling(20).mean()

    rsi = calc_rsi(close, RSI_PERIOD)
    signal = rsi.rolling(SIGNAL_PERIOD).mean()

    buy_signal = (rsi.shift(1) < signal.shift(1)) & (rsi >= signal)
    sell_signal = (rsi.shift(1) > signal.shift(1)) & (rsi <= signal)

    buy_dates = close[buy_signal].index
    sell_dates = close[sell_signal].index

    latest_buy = buy_dates[-1].strftime("%Y-%m-%d") if len(buy_dates) > 0 else "-"
    latest_sell = sell_dates[-1].strftime("%Y-%m-%d") if len(sell_dates) > 0 else "-"

    recent_buy = False
    if len(buy_dates) > 0:
        recent_buy = (close.index[-1] - buy_dates[-1]).days <= 10

    latest = {
        "close": close.iloc[-1],
        "ma20": ma20.iloc[-1],
        "ma60": ma60.iloc[-1],
        "rsi": rsi.iloc[-1],
        "signal": signal.iloc[-1],
        "volume": volume.iloc[-1],
        "avg_volume": avg_volume.iloc[-1],
        "latest_buy": latest_buy,
        "latest_sell": latest_sell,
        "recent_buy": recent_buy,
    }

    latest["final"] = judge_signal(
        latest["close"],
        latest["ma20"],
        latest["ma60"],
        latest["rsi"],
        latest["signal"],
        latest["volume"],
        latest["avg_volume"],
    )

    latest["score"] = score_stock(
        latest["close"],
        latest["ma20"],
        latest["ma60"],
        latest["rsi"],
        latest["signal"],
        latest["volume"],
        latest["avg_volume"],
        latest["recent_buy"],
    )

    return close, volume, ma20, ma60, rsi, signal, buy_signal, sell_signal, latest


@st.cache_data(ttl=60 * 60)
def load_yf_data(ticker, period="1y"):
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)

    if df.empty:
        return pd.DataFrame()

    close = df["Close"]
    volume = df["Volume"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]

    return pd.DataFrame({"Close": close, "Volume": volume}).dropna()


def scan_market():
    rows = []

    for name, ticker in SCAN_LIST.items():
        try:
            df = load_yf_data(ticker, "1y")

            if len(df) < 120:
                continue

            _, _, _, _, _, _, _, _, latest = analyze_df(df)

            if latest["final"] in ["🟢 강매수", "🟡 매수관심"]:
                rows.append({
                    "종목": name,
                    "현재가": round(latest["close"], 2),
                    "20일선": round(latest["ma20"], 2),
                    "60일선": round(latest["ma60"], 2),
                    "RSI": round(latest["rsi"], 2),
                    "Signal": round(latest["signal"], 2),
                    "거래량": int(latest["volume"]),
                    "평균거래량": int(latest["avg_volume"]),
                    "최근 매수": latest["latest_buy"],
                    "최근 매도": latest["latest_sell"],
                    "점수": latest["score"],
                    "판정": latest["final"],
                })

        except Exception:
            pass

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)
    return result.sort_values(by=["점수", "RSI"], ascending=[False, False])


tab1, tab2, tab3 = st.tabs(["📈 종목 분석", "🔎 매수 후보 스캐너", "🏆 강매수 TOP5"])

with tab2:
    st.subheader("🔎 43개 종목 매수 후보 스캐너")
    st.caption("조건: RSI(14) > Signal(6), 현재가 > 20일선 기준으로 매수 후보만 표시합니다.")

    if st.button("매수 후보 검색"):
        buy_df = scan_market()

        if buy_df.empty:
            st.warning("현재 매수 후보가 없습니다.")
        else:
            st.dataframe(buy_df, use_container_width=True)

with tab3:
    st.subheader("🏆 강매수 TOP5")
    st.caption("43개 종목 중 점수가 높은 상위 5개 종목입니다.")

    if st.button("TOP5 검색"):
        top_df = scan_market()

        if top_df.empty:
            st.warning("현재 TOP5 후보가 없습니다.")
        else:
            st.dataframe(top_df.head(5), use_container_width=True)

with tab1:
    st.subheader("📋 관심종목 현황판")

    summary = []

    for stock_name, ticker in WATCHLIST.items():
        try:
            df = load_yf_data(ticker, "1y")

            if len(df) < 120:
                continue

            _, _, _, _, _, _, _, _, latest = analyze_df(df)

            summary.append({
                "종목": stock_name,
                "현재가": round(latest["close"], 2),
                "RSI": round(latest["rsi"], 2),
                "Signal": round(latest["signal"], 2),
                "최근 매수": latest["latest_buy"],
                "최근 매도": latest["latest_sell"],
                "점수": latest["score"],
                "판정": latest["final"],
            })

        except Exception:
            pass

    st.dataframe(pd.DataFrame(summary), use_container_width=True)

    st.divider()

    st.subheader("🔍 선택 종목 상세 분석")

    name = st.selectbox("종목 선택", list(WATCHLIST.keys()))
    ticker = WATCHLIST[name]

    period = st.selectbox("조회 기간", ["6mo", "1y", "2y", "5y"], index=1)

    df = load_yf_data(ticker, period)

    if df.empty:
        st.error("데이터를 가져오지 못했습니다.")
    else:
        close, volume, ma20, ma60, rsi, signal, buy_signal, sell_signal, latest = analyze_df(df)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("현재가", f"{latest['close']:,.0f}")
        c2.metric("20일선", f"{latest['ma20']:,.0f}")
        c3.metric("60일선", f"{latest['ma60']:,.0f}")
        c4.metric("RSI(14)", f"{latest['rsi']:.2f}")
        c5.metric("Signal(6)", f"{latest['signal']:.2f}")

        c6, c7, c8, c9 = st.columns(4)
        c6.metric("거래량", f"{latest['volume']:,.0f}")
        c7.metric("평균거래량", f"{latest['avg_volume']:,.0f}")
        c8.metric("최근 매수신호", latest["latest_buy"])
        c9.metric("최근 매도신호", latest["latest_sell"])

        st.success(f"종합판정 : {latest['final']} / 점수 : {latest['score']}점")

        fig_price = go.Figure()

        fig_price.add_trace(go.Scatter(
            x=close.index,
            y=close,
            name="종가",
            line=dict(width=3)
        ))

        fig_price.add_trace(go.Scatter(
            x=ma20.index,
            y=ma20,
            name="20일선"
        ))

        fig_price.add_trace(go.Scatter(
            x=ma60.index,
            y=ma60,
            name="60일선"
        ))

        fig_price.add_trace(go.Scatter(
            x=close[buy_signal].index,
            y=close[buy_signal],
            mode="markers",
            name="매수",
            marker=dict(symbol="triangle-up", size=14)
        ))

        fig_price.add_trace(go.Scatter(
            x=close[sell_signal].index,
            y=close[sell_signal],
            mode="markers",
            name="매도",
            marker=dict(symbol="triangle-down", size=14)
        ))

        fig_price.update_layout(
            height=500,
            xaxis_title="날짜",
            yaxis_title="가격",
            hovermode="x unified"
        )

        st.plotly_chart(fig_price, use_container_width=True)

        st.subheader("RSI(14) + Signal(6)")

        fig_rsi = go.Figure()

        fig_rsi.add_trace(go.Scatter(
            x=rsi.index,
            y=rsi,
            name="RSI(14)",
            line=dict(width=3)
        ))

        fig_rsi.add_trace(go.Scatter(
            x=signal.index,
            y=signal,
            name="Signal(6)",
            line=dict(width=2)
        ))

        fig_rsi.add_hline(y=75, line_dash="dash", annotation_text="과매수 75")
        fig_rsi.add_hline(y=50, line_dash="dot", annotation_text="중립 50")
        fig_rsi.add_hline(y=35, line_dash="dash", annotation_text="과매도 35")

        fig_rsi.update_layout(
            height=450,
            yaxis=dict(range=[0, 100]),
            hovermode="x unified"
        )

        st.plotly_chart(fig_rsi, use_container_width=True)
