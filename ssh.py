import yfinance as ydatas
import pandas as pd
import ta
ticker = input("Enter code of stock(for example: THYAO): ").strip().upper()

df = ydatas.download(f"{ticker}.IS", period="6mo", auto_adjust=True, progress=False)

if df.empty:
    print(f"{ticker} no data found for this.")
else:
    #If MultiIndex exists,fix.
    if isinstance(df.columns,pd.MultiIndex):
        df.columns= df.columns.get_level_values(0)
    #Get only needed columns defined below:
    df =df[["Open","High","Low","Close","Volume"]]
    #Clear NaNs
    df.dropna(inplace=True)

    #ADX 
    df["ADX"]=ta.trend.ADXIndicator(df["High"],df["Low"],df["Close"],window=14).adx()
    #RSI
    df["RSI"]=ta.momentum.RSIIndicator(df["Close"],window=14).rsi()
    
    #EMA-10 Based Bollinger Band.
    ema=df["Close"].ewm(span=10,adjust=False).mean()
    std=df["Close"].rolling(window=20).std()
    df["BB_Upper"]=ema +2 * std
    df["BB_Lower"]=ema -2 * std

    #ATR:Needed for Keltner
    df["ATR"]=ta.volatility.AverageTrueRange(df["High"],df["Low"],df["Close"],window=14).average_true_range()

    #Keltner Channel
    kc_mid=df["Close"].ewm(span=20,adjust=False).mean()
    df["KC_Upper"]=kc_mid +1.5 *df["ATR"]
    df["KC_Lower"]=kc_mid -1.5 *df["ATR"]
    df.dropna(inplace=True)

    adx = round(float(df["ADX"].iloc[-1]),2)
    rsi = round(float(df["RSI"].iloc[-1]),2) 
    bb =df["BB_Upper"].iloc[-1] < df["KC_Upper"].iloc[-1] and \
        df["BB_Lower"].iloc[-1] > df["KC_Lower"].iloc[-1]

    no_trend=adx <20
    rsi_flat =40 <=rsi <=60
    print(f"ADX:{adx} →{'There is no trend,stock is squeezed' if adx <20 else 'A trend exists'}")
    print(f"RSI: {rsi} → {'Squeeze band' if rsi_flat else 'Not squeezed'}")
    print(f"BB inside Keltner Channel: {'Yes' if bb else 'no'}")

    if no_trend and rsi_flat and bb:
        print("\n Squeeze is detected!")
    else:
        print("\n No squeeze.")
    # --- Last month's squeeze history --- 
    last_month = df[df.index >= df.index[-1] - pd.Timedelta(days=30)]
    print(f"\n--- Last month's squeeze history ---") 
    squeeze_count = 0 
    for date, row in last_month.iterrows(): 
        adx_d = round(float(row["ADX"]), 2) 
        rsi_d = round(float(row["RSI"]), 2) 
        bb_d=row["BB_Upper"] < row["KC_Upper"] and row["BB_Lower"] > row ["KC_Lower"]
        is_squeeze = adx_d < 20 and 40 <= rsi_d <= 60 and bb_d 
        if is_squeeze: 
            squeeze_count += 1 
            print(f"{date.strftime('%d.%m.%Y')}: Squeeze  RSI: {rsi_d}  ADX: {adx_d}") 
    print(f"\nTotal {squeeze_count} days squeezed.") 
