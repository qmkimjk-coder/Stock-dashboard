import streamlit as st
import yfinance as yf
import pandas as pd

st.title("주식 RSI 대시보드")

ticker = st.text_input("종목코드", "005930.KS")

data = yf.download(ticker, period="6mo")

delta = data["Close"].diff()

gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))

st.line_chart(data["Close"])
st.line_chart(rsi)

st.write("현재 RSI:", round(float(rsi.iloc[-1]), 2))
