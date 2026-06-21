import streamlit as st
import yfinance as yf
import pandas as pd

st.title("주식 RSI 대시보드")

stock_dict = {
    "삼성전자": "005930.KS",
    "삼성전자우": "005935.KS",
    "KT": "030200.KS",
    "SK하이닉스": "000660.KS"
}

name = st.selectbox("종목 선택", list(stock_dict.keys()))
ticker = stock_dict[name]

data = yf.download(ticker, period="1y", auto_adjust=True, progress=False)

if data.empty:
    st.error("데이터를 가져오지 못했습니다. 잠시 후 다시 시도하거나 다른 종목을 선택하세요.")
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

    st.subheader(f"{name} 종가 차트")
    st.line_chart(close)

    st.subheader("RSI(14)")
    st.line_chart(rsi)

    latest_close = close.dropna().iloc[-1]
    latest_rsi = rsi.dropna().iloc[-1]

    st.write("최근 종가:", round(float(latest_close), 0))
    st.write("현재 RSI:", round(float(latest_rsi), 2))
