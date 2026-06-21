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
    "SK하이닉스": "000660.KS"
}

name = st.selectbox("종목 선택", list(stocks.keys()))
ticker = stocks[name]

data = yf.download(ticker, period="1y", auto_adjust=True, progress=False)

if data.empty:
    st.error("데이터를 가져오지 못했습니다.")
else:
    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    latest_close = close.dropna().iloc[-1]
    latest_rsi = rsi.dropna().iloc[-1]

    col1, col2 = st.columns(2)
    col1.metric("최근 종가", f"{latest_close:,.0f} 원")
    col2.metric("현재 RSI(14)", f"{latest_rsi:.2f}")

    st.subheader(f"{name} 종가 차트")

    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(
        x=close.index,
        y=close,
        mode="lines",
        name="종가",
        line=dict(width=3)
    ))
    fig_price.update_layout(
        height=450,
        xaxis_title="날짜",
        yaxis_title="가격",
        hovermode="x unified"
    )
    st.plotly_chart(fig_price, use_container_width=True)

    st.subheader("RSI(14)")

    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(
        x=rsi.index,
        y=rsi,
        mode="lines",
        name="RSI(14)",
        line=dict(width=3)
    ))

    fig_rsi.add_hline(y=70, line_dash="dash", annotation_text="과매수 70")
    fig_rsi.add_hline(y=30, line_dash="dash", annotation_text="과매도 30")
    fig_rsi.add_hline(y=50, line_dash="dot", annotation_text="중립 50")

    fig_rsi.update_layout(
        height=400,
        xaxis_title="날짜",
        yaxis_title="RSI",
        yaxis=dict(range=[0, 100]),
        hovermode="x unified"
    )
    st.plotly_chart(fig_rsi, use_container_width=True)
