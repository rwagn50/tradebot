import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time

def fetch_stock_data(ticker, start_date=None, end_date=None, interval='1d'):
    if interval != '1d':
        period_map = {'1m': '7d', '5m': '60d', '15m': '60d', '30m': '60d', '60m': '730d'}
        period = period_map.get(interval, '7d')
        data = yf.download(ticker, period=period, interval=interval)
    else:
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    return data

def moving_average_crossover(data, short_window=50, long_window=200):
    data['Short_MA'] = data['Close'].rolling(window=short_window).mean()
    data['Long_MA'] = data['Close'].rolling(window=long_window).mean()
    data['Signal'] = 0
    data['Signal'][short_window:] = (data['Short_MA'][short_window:] > data['Long_MA'][short_window:]).astype(int)
    data['Signal'].fillna(0, inplace=True)
    data['Position'] = data['Signal'].diff()
    data['Position'].fillna(0, inplace=True)
    return data

def simulate_trades(data, initial_capital=10000, ticker=""):
    hold_position = 0
    capital = initial_capital
    shares = 0
    trades = []
    for i in range(len(data)):
        if data['Position'].iloc[i] == 1 and hold_position == 0:
            shares = capital / data['Close'].iloc[i]
            capital = 0
            hold_position = 1
            trades.append(f"{ticker} Buy at {data.index[i]}: {data['Close'].iloc[i]:.2f}, shares: {shares:.2f}")
        elif data['Position'].iloc[i] == -1 and hold_position == 1:
            trades.append(f"{ticker} Sell at {data.index[i]}: {data['Close'].iloc[i]:.2f}, shares: {shares:.2f}")
            capital = shares * data['Close'].iloc[i]
            shares = 0
            hold_position = 0
    if hold_position == 1:
        final_value = shares * data['Close'].iloc[-1]
    else:
        final_value = capital
    return trades, final_value, hold_position

def calculate_performance(initial_capital, final_value, data):
    total_return = (final_value / initial_capital - 1) * 100
    total_days = (data.index[-1] - data.index[0]).days
    if total_days > 0:
        annualized_return = (final_value / initial_capital) ** (365 / total_days) - 1
        annualized_return *= 100
    else:
        annualized_return = 0
    return total_return, annualized_return

def get_imminent_trade(data, hold_position, ticker):
    if len(data) < 2:
        return ""
    # Look at the last two positions to see if there's a new signal
    last_position = data['Position'].iloc[-1]
    prev_position = data['Position'].iloc[-2]
    last_close = data['Close'].iloc[-1]
    date = data.index[-1]
    if last_position == 1 and hold_position == 0:
        return f"{ticker} Buy signal at {date}: {last_close:.2f}"
    elif last_position == -1 and hold_position == 1:
        return f"{ticker} Sell signal at {date}: {last_close:.2f}"
    else:
        return "No imminent trade signal."

# Streamlit UI
st.title("Moving Average Crossover TradeBot")

ticker = st.text_input("Enter stock ticker (e.g., AAPL):", "AAPL")
start_date = st.date_input("Start date", datetime.now() - timedelta(days=365))
end_date = st.date_input("End date", datetime.now())
short_window = st.number_input("Short moving average window", value=50, min_value=1)
long_window = st.number_input("Long moving average window", value=200, min_value=2)
initial_capital = st.number_input("Initial capital ($)", value=10000)

if st.button("Run Backtest"):
    data = fetch_stock_data(ticker, start_date, end_date)
    if data.empty:
        st.error("No data fetched. Try a different ticker or date range.")
    else:
        data = moving_average_crossover(data, short_window, long_window)
        trades, final_value, hold_position = simulate_trades(data, initial_capital, ticker)
        total_return, annualized_return = calculate_performance(initial_capital, final_value, data)
        imminent_trade = get_imminent_trade(data, hold_position, ticker)

        st.subheader("Trade Log")
        for trade in trades:
            st.write(trade)
        st.subheader("Performance")
        st.write(f"Total Return: {total_return:.2f}%")
        st.write(f"Annualized Return: {annualized_return:.2f}%")
        st.write(f"Final Value: ${final_value:.2f}")
        st.subheader("Imminent Trade Signal")
        st.write(imminent_trade)

        st.subheader("Chart")
        st.line_chart(data[['Close', 'Short_MA', 'Long_MA']])
