import yfinance as ydatas
import pandas as pd
import ta
import datetime
import time


def prepare_data(tickers_file="tickers.txt", lookback_days=730, progress_callback=None):
    """
    Tum hisseleri indirir, indikatorleri hesaplar, hazir DataFrame'leri doner.
    Bu fonksiyon threshold/target'tan bagimsizdir - bir kere cagir, sonuclari cache'le.
    """
    with open(tickers_file, "r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]

    total = len(tickers)
    end = datetime.date.today()
    start = end - datetime.timedelta(days=lookback_days)
    tickers_with_is = [f"{t}.IS" for t in tickers]

    chunk_size = 50
    all_data_frames = []

    print("Veri indiriliyor...")
    for i in range(0, len(tickers_with_is), chunk_size):
        chunk = tickers_with_is[i:i + chunk_size]
        chunk_data = ydatas.download(
            chunk, start=start, end=end, auto_adjust=True,
            group_by='ticker', progress=False, threads=True
        )
        if not chunk_data.empty:
            all_data_frames.append(chunk_data)
        if progress_callback:
            progress_callback(f"Indiriliyor: {min(i+chunk_size, len(tickers_with_is))}/{len(tickers_with_is)}")
        time.sleep(1.5)

    if not all_data_frames:
        return {"data": {}, "tickers": tickers, "failed": tickers, "total": total}

    data = pd.concat(all_data_frames, axis=1)
    data.index = data.index.tz_localize(None)

    prepared = {}
    failed_tickers = []

    print("Indikatorler hesaplaniyor...")
    counter = 0
    for ticker in tickers:
        counter += 1
        if progress_callback and counter % 50 == 0:
            progress_callback(f"Hazirlaniyor: {counter}/{total}")

        try:
            yf_ticker = f"{ticker}.IS"
            if isinstance(data.columns, pd.MultiIndex):
                if yf_ticker not in data.columns.levels[0]:
                    failed_tickers.append(ticker)
                    continue
                df = data[yf_ticker].copy()
            else:
                df = data.copy()

            df.dropna(inplace=True)
            if df.empty or len(df) < 25:
                failed_tickers.append(ticker)
                continue

            df["ADX"] = ta.trend.ADXIndicator(df["High"], df["Low"], df["Close"], window=14).adx()
            df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()

            ema = df["Close"].ewm(span=10, adjust=False).mean()
            std = df["Close"].rolling(window=20).std()
            df["BB_Upper"] = ema + 2 * std
            df["BB_Lower"] = ema - 2 * std

            df["ATR"] = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"], window=14).average_true_range()
            kc_mid = df["Close"].ewm(span=20, adjust=False).mean()
            df["KC_Upper"] = kc_mid + 1.5 * df["ATR"]
            df["KC_Lower"] = kc_mid - 1.5 * df["ATR"]

            df["RANGE"] = df["High"] - df["Low"]
            df["RANGE_3D"] = df["RANGE"].rolling(3).mean()

            df.dropna(inplace=True)
            if df.empty:
                failed_tickers.append(ticker)
                continue

            prepared[ticker] = df

        except Exception:
            failed_tickers.append(ticker)

    return {
        "data": prepared,
        "tickers": tickers,
        "failed": failed_tickers,
        "total": total
    }


def run_backtest(prepared, mode="percentile", percentile_threshold=0.25, target_pct=0.15, hold_days=21):
    """
    Hazirlanmis data ustunde squeeze condition ve backtest calistirir.
    Hizli - veri indirme/indikator hesaplama yapmaz.
    """
    cutoff = pd.Timestamp(datetime.date.today()) - pd.Timedelta(days=30)
    global_stats = {"signals": 0, "wins": 0, "sum_breakout": 0.0, "sum_days": 0.0}
    squeeze_now_list = []
    squeezed_last_month_list = []

    for ticker, df in prepared["data"].items():
        try:
            adx = round(float(df["ADX"].iloc[-1]), 2)
            rsi = round(float(df["RSI"].iloc[-1]), 2)
            bb = (df["BB_Upper"].iloc[-1] < df["KC_Upper"].iloc[-1] and
                  df["BB_Lower"].iloc[-1] > df["KC_Lower"].iloc[-1])

            no_trend = adx < 20
            rsi_flat = 40 <= rsi <= 60

            if mode == "percentile":
                last3_range = df["RANGE"].iloc[-3:].mean()
                current_threshold = df["RANGE"].iloc[-20:].quantile(percentile_threshold)
                squeeze_now = no_trend and rsi_flat and (last3_range < current_threshold)

                historical_threshold = df["RANGE"].rolling(20).quantile(percentile_threshold)
                squeeze_cond = (
                    (df["ADX"] < 20) &
                    (df["RSI"].between(40, 60)) &
                    (df["RANGE_3D"] < historical_threshold)
                )
            else:
                squeeze_now = no_trend and rsi_flat and bb
                squeeze_cond = (
                    (df["ADX"] < 20) &
                    (df["RSI"].between(40, 60)) &
                    (df["BB_Upper"] < df["KC_Upper"]) &
                    (df["BB_Lower"] > df["KC_Lower"])
                )

            squeeze_starts = squeeze_cond & ~squeeze_cond.shift(1, fill_value=False)
            testable_starts = squeeze_starts.iloc[:-hold_days]

            ticker_wins = 0
            ticker_signals = 0

            for idx in testable_starts[testable_starts].index:
                ticker_signals += 1
                global_stats["signals"] += 1

                entry_price = df.loc[idx, "Close"]
                target_price = entry_price * (1 + target_pct)

                start_pos = df.index.get_loc(idx)
                end_pos = min(start_pos + hold_days + 1, len(df))
                window = df.iloc[start_pos + 1: end_pos]

                if window.empty:
                    continue

                max_high = window["High"].max()
                global_stats["sum_breakout"] += ((max_high / entry_price) - 1) * 100

                if max_high >= target_price:
                    ticker_wins += 1
                    global_stats["wins"] += 1
                    target_reached_window = window[window["High"] >= target_price]
                    first_target_idx = target_reached_window.index[0]
                    global_stats["sum_days"] += (first_target_idx - idx).days

            ticker_win_rate = (ticker_wins / ticker_signals * 100) if ticker_signals > 0 else 0
            squeeze_count = int(squeeze_cond.loc[df.index >= cutoff].sum())

            if squeeze_now and squeeze_count >= 3:
                squeeze_now_list.append({
                    "Ticker": ticker, "ADX": adx, "RSI": rsi,
                    "Win Rate": f"%{ticker_win_rate:.1f}",
                    "30d Squeeze Days": squeeze_count
                })
            if squeeze_count >= 3:
                squeezed_last_month_list.append({
                    "Ticker": ticker, "ADX": adx, "RSI": rsi,
                    "Win Rate": f"%{ticker_win_rate:.1f}",
                    "30d Squeeze Days": squeeze_count
                })

        except Exception:
            continue

    return {
        "squeeze_now_list": squeeze_now_list,
        "squeezed_last_month_list": squeezed_last_month_list,
        "global_stats": global_stats
    }


def run_scan(progress_callback=None, mode="classic", percentile_threshold=0.25, target_pct=0.15):
    """Eski API - geriye uyumluluk icin."""
    prepared = prepare_data()
    result = run_backtest(
        prepared, mode=mode,
        percentile_threshold=percentile_threshold,
        target_pct=target_pct
    )
    return (
        result["squeeze_now_list"],
        result["squeezed_last_month_list"],
        prepared["failed"],
        prepared["total"],
        result["global_stats"]
    )