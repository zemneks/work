import time
import datetime
import yfinance as yf
import telebot
import pandas as pd

# Telegram Bot Token
TELEGRAM_TOKEN = '8096066446:AAEmHYj0TDOljFjrq4E-avfOP9cEoUfr9Uk'
CHAT_ID = '195089851'
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Load instruments from file
with open('instruments.txt', 'r') as file:
    instruments = [line.strip() for line in file.readlines()]

# Calculate Heiken Ashi candles
def calculate_heiken_ashi(df):
    ha_df = pd.DataFrame()
    ha_df['close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    ha_df['open'] = (df['Open'].shift(1) + df['Close'].shift(1)) / 2
    ha_df['high'] = df[['High', 'open', 'close']].max(axis=1)
    ha_df['low'] = df[['Low', 'open', 'close']].min(axis=1)
    ha_df['open'].fillna(ha_df['close'], inplace=True)
    return ha_df

# Check if conditions are met
def check_strategy(ticker):
    data = {}
    for timeframe, period in {'1h': '60m', '1d': '1d', '1w': '1wk'}.items():
        df = yf.download(ticker, interval=period, period='3mo')
        df = df[['Open', 'High', 'Low', 'Close']]
        data[timeframe] = calculate_heiken_ashi(df)

    if len(data['1w']) < 2 or len(data['1d']) < 2 or len(data['1h']) < 2:
        return False

    weekly_direction = data['1w'].iloc[-2]['close'] > data['1w'].iloc[-2]['open']
    daily_direction = data['1d'].iloc[-2]['close'] > data['1d'].iloc[-2]['open']
    hourly_direction = data['1h'].iloc[-2]['close'] > data['1h'].iloc[-2]['open']

    return weekly_direction == daily_direction and weekly_direction != hourly_direction

# Main loop
while True:
    now = datetime.datetime.utcnow()
    if now.weekday() in [5, 6]:  # Skip weekends
        time.sleep(60)
        continue

    if now.minute == 59:  # Run at HH:59
        for instrument in instruments:
            try:
                if check_strategy(instrument):
                    message = f"Стратегия выполнена для {instrument}!"
                    bot.send_message(CHAT_ID, message)
            except Exception as e:
                bot.send_message(CHAT_ID, f"Ошибка для {instrument}: {e}")
        
        time.sleep(60)  # Wait a minute to avoid duplicate runs

    time.sleep(1)
