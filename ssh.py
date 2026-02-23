import yfinance as ydatas

ticker = input("Hisse kodu girin (örn: THYAO): ").strip().upper()

df = ydatas.download(f"{ticker}.IS", period="6mo", auto_adjust=True, progress=False)

if df.empty:
    print(f"{ticker} için veri bulunamadı.")
else:
    print(df.tail(10))