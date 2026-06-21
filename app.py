import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from pykrx import stock
from datetime import datetime, timedelta

st.set_page_config(page_title="주식 투자 대시보드", layout="wide")
st.title("📈 주식 투자 대시보드")

RSI_PERIOD = 14
SIGNAL_PERIOD = 6


WATCHLIST = {
    "삼성전자": "005930.KS",
    "삼성전자우": "005935.KS",
    "KT": "030200.KS",
    "SK하이닉스": "000660.KS",
    "NAVER": "035420.KS",
    "현대차": "005380.KS",
    "SOXL": "SOXL",
    "NVDA": "NVDA",
    "PLTR": "PLTR"
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
    elif rsi < signal and close < ma20 and ma20 < ma60 and volume > avg_volume:
        return "⚫ 하락추세"
    elif rsi < signal and close < ma20:
        return "🔴 약세전환"
    else:
        return "🟠 관망"


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

    latest = {
        "close": close.iloc[-1],
        "ma20": ma20.iloc[-1],
        "ma60": ma60.iloc[-1],
        "rsi": rsi.iloc[-1],
        "signal": signal.iloc[-1],
        "volume": volume.iloc[-1],
        "avg_volume": avg_volume.iloc[-1],
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

    buy_dates = close[buy_signal].index
    sell_dates = close[sell_signal].index

    latest["latest_buy"] = buy_dates[-1].strftime("%Y-%m-%d") if len(buy_dates) > 0 else "-"
    latest["latest_sell"] = sell_dates[-1].strftime("%Y-%m-%d") if len(sell_dates) > 0 else "-"

    return close, volume, ma20, ma60, rsi, signal, buy_signal, sell_signal, latest


@st.cache_data(ttl=60 * 60 * 6)
def get_kospi200_candidates():
    today = datetime.today()
    end = today.strftime("%Y%m%d")
    start = (today - timedelta(days=420)).strftime("%Y%m%d")

    tickers = stock.get_index_portfolio_deposit_file("1028")
    result = []

    progress = st.progress(0)

    for i, ticker in enumerate(tickers):
        try:
            name = stock.get_market_ticker_name(ticker)
            df = stock.get_market_ohlcv_by_date(start, end, ticker)

            if len(df) < 120:
                continue

            df = df.rename(
                columns={
                    "종가": "Close",
                    "거래량": "Volume"
                }
            )

            df = df[["Close", "Volume"]].dropna()

            close, volume, ma20, ma60, rsi, signal, buy_signal, sell_signal, latest = analyze_df(df)

            if latest["final"] in ["🟢 강매수", "🟡 매수관심"]:
                result.append({
                    "종목코드": ticker,
                    "종목명": name,
                    "현재가": round(latest["close"], 0),
                    "20일선": round(latest["ma20"], 0),
                    "60일선": round(latest["ma60"], 0),
                    "RSI": round(latest["rsi"], 2),
                    "Signal": round(latest["signal"], 2),
                    "거래량": int(latest["volume"]),
                    "평균거래량": int(latest["avg_volume"]),
                    "최근 매수": latest["latest_buy"],
                    "최근 매도": latest["latest_sell"],
                    "판정": latest["final"],
                })

        except Exception:
            pass

        progress.progress((i + 1) / len(tickers))

    progress.empty()

    return pd.DataFrame(result)


st.subheader("🔎 KOSPI200 조건 부합 종목 추천")

if st.button("KOSPI200 스캔 실행"):
    candidates = get_kospi200_candidates()

    if candidates.empty:
        st.warning("현재 조건에 부합하는 종목이 없습니다.")
    else:
        candidates = candidates.sort_values(
            by=["판정", "RSI"],
            ascending=[True, False]
        )
        st.dataframe(candidates, use_container_width=True)

st.divider()


st.subheader("📋 관심종목 현황판")

summary = []

for stock_name, ticker in WATCHLIST.items():
    try:
        df = yf.download(ticker, period="1y", auto_adjust=True, progress=False)

        if df.empty:
            continue

        close = df["Close"]
        volume = df["Volume"]

        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        if isinstance(volume, pd.DataFrame):
            volume = volume.iloc[:, 0]

        df2 = pd.DataFrame({
            "Close": close,
            "Volume": volume
        }).dropna()

        _, _, _, _, _, _, _, _, latest = analyze_df(df2)

        summary.append({
            "종목": stock_name,
            "현재가": round(latest["close"], 0),
            "RSI": round(latest["rsi"], 2),
            "Signal": round(latest["signal"], 2),
            "최근 매수": latest["latest_buy"],
            "최근 매도": latest["latest_sell"],
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

data = yf.download(ticker, period=period, auto_adjust=True, progress=False)

if data.empty:
    st.error("데이터를 가져오지 못했습니다.")
else:
    close = data["Close"]
    volume = data["Volume"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]

    df = pd.DataFrame({
        "Close": close,
        "Volume": volume
    }).dropna()

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

    st.success(f"종합판정 : {latest['final']}")

    fig_price = go.Figure()

    fig_price.add_trace(go.Scatter(x=close.index, y=close, name="종가", line=dict(width=3)))
    fig_price.add_trace(go.Scatter(x=ma20.index, y=ma20, name="20일선"))
    fig_price.add_trace(go.Scatter(x=ma60.index, y=ma60, name="60일선"))

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

    fig_price.update_layout(height=500, hovermode="x unified")
    st.plotly_chart(fig_price, use_container_width=True)

    fig_rsi = go.Figure()

    fig_rsi.add_trace(go.Scatter(x=rsi.index, y=rsi, name="RSI(14)", line=dict(width=3)))
    fig_rsi.add_trace(go.Scatter(x=signal.index, y=signal, name="Signal(6)", line=dict(width=2)))

    fig_rsi.add_hline(y=75, line_dash="dash", annotation_text="과매수 75")
    fig_rsi.add_hline(y=50, line_dash="dot", annotation_text="중립 50")
    fig_rsi.add_hline(y=35, line_dash="dash", annotation_text="과매도 35")

    fig_rsi.update_layout(height=450, yaxis=dict(range=[0, 100]), hovermode="x unified")
    st.plotly_chart(fig_rsi, use_container_width=True)
