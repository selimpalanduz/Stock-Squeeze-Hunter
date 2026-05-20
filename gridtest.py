"""
Grid search: Threshold x Target kombinasyonlarini test eder.
Hizli versiyon - data 1 kez indirilir, indikatorler 1 kez hesaplanir,
sonra her kombinasyon icin sadece backtest tekrar calisir.
"""
import pandas as pd
import time
from sshnew import prepare_data, run_backtest

# --- TEST PARAMETERS ---
THRESHOLDS = [0.10, 0.15, 0.20, 0.25, 0.30]
TARGETS = [0.06, 0.08, 0.10, 0.12, 0.15, 0.20]
HOLD_DAYS = 21


def progress(msg):
    print(f"  {msg}")


print("=" * 70)
print("ADIM 1/2: Veri hazirlaniyor (bir kere)")
print("=" * 70)
t0 = time.time()
prepared = prepare_data(progress_callback=progress)
print(f"\nHazirlandi: {len(prepared['data'])} hisse OK, "
      f"{len(prepared['failed'])} hisse FAIL")
print(f"Sure: {time.time()-t0:.1f} sn")

print("\n" + "=" * 70)
print(f"ADIM 2/2: Grid test ({len(THRESHOLDS)}x{len(TARGETS)} = "
      f"{len(THRESHOLDS)*len(TARGETS)} kombinasyon)")
print("=" * 70)

results = []
total_combos = len(THRESHOLDS) * len(TARGETS)
combo_counter = 0

for thresh in THRESHOLDS:
    for target in TARGETS:
        combo_counter += 1
        t1 = time.time()
        
        result = run_backtest(
            prepared,
            mode="percentile",
            percentile_threshold=thresh,
            target_pct=target,
            hold_days=HOLD_DAYS
        )
        stats = result["global_stats"]
        
        win_rate = (stats["wins"] / stats["signals"] * 100) if stats["signals"] > 0 else 0
        avg_breakout = stats["sum_breakout"] / stats["signals"] if stats["signals"] > 0 else 0
        avg_days = stats["sum_days"] / stats["wins"] if stats["wins"] > 0 else 0
        expected_return = win_rate / 100 * (target * 100)
        
        results.append({
            "Threshold": thresh,
            "Target": target,
            "Target_Str": f"%{target*100:.0f}",
            "Signals": stats["signals"],
            "Wins": stats["wins"],
            "Win_Rate": round(win_rate, 1),
            "Win_Rate_Str": f"%{win_rate:.1f}",
            "Avg_Breakout": round(avg_breakout, 2),
            "Avg_Days": round(avg_days, 1),
            "Expected_Return": round(expected_return, 2),
            "Expected_Return_Str": f"%{expected_return:.2f}"
        })
        
        print(f"  [{combo_counter}/{total_combos}] thresh={thresh}, "
              f"target=%{target*100:.0f} -> "
              f"win=%{win_rate:.1f}, exp=%{expected_return:.2f}/trade "
              f"({time.time()-t1:.1f}s)")

df = pd.DataFrame(results)
df.to_csv("grid_results_full.csv", index=False)

print("\n" + "=" * 70)
print("EXPECTED RETURN PIVOT (asil bakman gereken)")
print("=" * 70)
pivot_er = df.pivot(index="Threshold", columns="Target_Str", values="Expected_Return")
print(pivot_er)

print("\n" + "=" * 70)
print("WIN RATE PIVOT")
print("=" * 70)
pivot_wr = df.pivot(index="Threshold", columns="Target_Str", values="Win_Rate")
print(pivot_wr)

print("\n" + "=" * 70)
print("SIGNAL COUNT PIVOT")
print("=" * 70)
pivot_sig = df.pivot(index="Threshold", columns="Target_Str", values="Signals")
print(pivot_sig)

# Best 5 combinations by Expected Return
print("\n" + "=" * 70)
print("BEST 5 COMBINATIONS (by Expected Return)")
print("=" * 70)
top5 = df.nlargest(5, "Expected_Return")[
    ["Threshold", "Target_Str", "Signals", "Win_Rate_Str", "Expected_Return_Str", "Avg_Days"]
]
print(top5.to_string(index=False))

print(f"\nToplam sure: {time.time()-t0:.1f} sn")
print("Results saved to grid_results_full.csv.")