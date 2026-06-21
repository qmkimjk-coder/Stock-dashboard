import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="주식 RSI 대시보드", layout="wide")

st.title("주식 RSI 대시보드")

stocks = {
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

name = st.selectbox("종목 선택", list(stocks.keys()))
ticker = stocks[name]

period = st.selectbox("기간 선택", ["6mo", "1y", "2y", "5y"], index=1)

rsi_period = 14
signal_period = 6

data = yf.download(ticker, period=period, auto_adjust=True, progress=False)

if data.empty:
    st.error("데이터를 가져오지 못했습니다.")
else:
    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / rsi_period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / rsi_period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    signal = rsi.rolling(signal_period).mean()

    buy_signal = (rsi.shift(1) < signal.shift(1)) & (rsi >= signal)
    sell_signal = (rsi.shift(1) > signal.shift(1)) & (rsi <= signal)

    latest_close = close.dropna().iloc[-1]
    latest_rsi = rsi.dropna().iloc[-1]
    latest_signal = signal.dropna().iloc[-1]

    if latest_rsi > latest_signal:
        status = "RSI > Signal / 상승 우위"
    elif latest_rsi < latest_signal:
        status = "RSI < Signal / 하락 우위"
    else:
        status = "중립"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("최근 종가", f"{latest_close:,.0f}")
    col2.metric("RSI(14)", f"{latest_rsi:.2f}")
    col3.metric("Signal(6)", f"{latest_signal:.2f}")
    col4.metric("현재 상태", status)

    st.subheader(f"{name} 종가 차트")

    fig_price = go.Figure()

    fig_price.add_trace(go.Scatter(
        x=close.index,
        y=close,
        mode="lines",
        name="종가",
        line=dict(width=3)
    ))

    fig_price.add_trace(go.Scatter(
        x=close[buy_signal].index,
        y=close[buy_signal],
        mode="markers",
        name="매수 신호",
        marker=dict(symbol="triangle-up", size=14)
    ))

    fig_price.add_trace(go.Scatter(
        x=close[sell_signal].index,
        y=close[sell_signal],
        mode="markers",
        name="매도 신호",
        marker=dict(symbol="triangle-down", size=14)
    ))

    fig_price.update_layout(
        height=450,
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
        mode="lines",
        name="RSI(14)",
        line=dict(width=3)
    ))

    fig_rsi.add_trace(go.Scatter(
        x=signal.index,
        y=signal,
        mode="lines",
        name="Signal(6)",
        line=dict(width=2, dash="dot")
    ))

    fig_rsi.add_trace(go.Scatter(
        x=rsi[buy_signal].index,
        y=rsi[buy_signal],
        mode="markers",
        name="매수 신호",
        marker=dict(symbol="triangle-up", size=14)
    ))

    fig_rsi.add_trace(go.Scatter(
        x=rsi[sell_signal].index,
        y=rsi[sell_signal],
        mode="markers",
        name="매도 신호",
        marker=dict(symbol="triangle-down", size=14)
    ))

    fig_rsi.add_hline(y=75, line_dash="dash", annotation_text="과매수 참고 75")
    fig_rsi.add_hline(y=50, line_dash="dot", annotation_text="중립 50")
    fig_rsi.add_hline(y=35, line_dash="dash", annotation_text="과매도 참고 35")

    fig_rsi.update_layout(
        height=420,
        xaxis_title="날짜",
        yaxis_title="RSI",
        yaxis=dict(range=[0, 100]),
        hovermode="x unified"
    )

    st.plotly_chart(fig_rsi, use_container_width=True)

    st.info(
        "매수 신호: RSI(14)가 Signal(6)을 상향 돌파 / "
        "매도 신호: RSI(14)가 Signal(6)을 하향 돌파 / "
        "75 이상은 과매수 참고, 35 이하는 과매도 참고"
    )
