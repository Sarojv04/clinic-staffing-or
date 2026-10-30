"""Run the whole project end to end:
forecast demand -> optimize shifts (PuLP) -> simulate the clinic (SimPy) -> what-if scenario.
Results are printed and saved to the outputs/ folder."""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import DAYS, HOURS, SIM_REPLICATIONS, SCENARIO_DEMAND_GROWTH, WAIT_TARGET_MIN, WEEKS_OF_HISTORY
from data import make_history, true_rate
from forecast import seasonal_forecast, backtest
from optimize import staff_required, solve_schedule, flat_schedule
from simulate import simulate_week

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
os.makedirs(OUT, exist_ok=True)


def line(t=""):
    print(t)
    report.append(t)


report = []

# ---------- 1. Data ----------
history = make_history()
history.to_csv(os.path.join(OUT, "patient_arrivals_history.csv"), index=False)
line("# Clinic Staffing: Forecast -> Optimize -> Simulate")
line()
line(f"History: {WEEKS_OF_HISTORY} weeks, {history.arrivals.sum():,} synthetic patient arrivals")

# ---------- 2. Forecast ----------
errors = backtest(history)
fc = seasonal_forecast(history)
fc.to_csv(os.path.join(OUT, "forecast_next_week.csv"), index=False)
line()
line("## 1. Forecast (hold-out test on the last week, mean absolute error, patients/hour)")
for k, v in errors.items():
    line(f"- {k}: {v:.2f}")
line(f"- Forecast for next week: {fc.forecast.sum():.0f} patients")

# ---------- 3. Optimize ----------
required = staff_required(fc)
opt = solve_schedule(required)
flat = flat_schedule(required, "peak")
flat_avg = flat_schedule(required, "average")
pd.DataFrame(opt["roster"]).sort_values(["day", "start"], key=lambda s: s.map(DAYS.index) if s.name == "day" else s) \
    .to_csv(os.path.join(OUT, "optimized_roster.csv"), index=False)
line()
line("## 2. Optimization (PuLP integer program)")
line(f"- Solver status: {opt['status']}")
line(f"- Optimized schedule: ${opt['cost']:,.0f}/week, {opt['paid_hours']} paid staff-hours")
line(f"- Flat schedule sized to the peak hour: ${flat['cost']:,.0f}/week, {flat['paid_hours']} paid staff-hours")
line(f"- Flat schedule sized to the average hour: ${flat_avg['cost']:,.0f}/week, {flat_avg['paid_hours']} paid staff-hours")
line(f"- Saving vs. peak-sized flat schedule: ${flat['cost'] - opt['cost']:,.0f}/week ({(flat['cost'] - opt['cost']) / flat['cost']:.0%})")

# ---------- 4. Simulate ----------
# Test both schedules against the TRUE demand of next week (not the forecast), so forecast error is included.
actual_rates = {(d, h): true_rate(d, h, WEEKS_OF_HISTORY) for d in DAYS for h in HOURS}
sim_opt = simulate_week(actual_rates, opt["staffing"], SIM_REPLICATIONS, seed=1)
sim_flat = simulate_week(actual_rates, flat["staffing"], SIM_REPLICATIONS, seed=1)
sim_flat_avg = simulate_week(actual_rates, flat_avg["staffing"], SIM_REPLICATIONS, seed=1)
line()
line(f"## 3. Simulation (SimPy, {SIM_REPLICATIONS} simulated weeks each)")
line(f"| Schedule | Cost/week | Avg wait (min) | 90th pct wait (min) | Seen within {WAIT_TARGET_MIN} min |")
line("|---|---|---|---|---|")
for name, p, s in [("Optimized (PuLP)", opt, sim_opt), ("Flat - peak-sized", flat, sim_flat),
                   ("Flat - average-sized", flat_avg, sim_flat_avg)]:
    line(f"| {name} | ${p['cost']:,.0f} | {s['avg_wait']:.1f} | {s['p90_wait']:.1f} | {s['pct_within_target']:.0%} |")

# ---------- 5. What-if scenario ----------
g = 1 + SCENARIO_DEMAND_GROWTH
fc_up = fc.assign(forecast=fc.forecast * g)
opt_up = solve_schedule(staff_required(fc_up))
rates_up = {k: v * g for k, v in actual_rates.items()}
sim_keep = simulate_week(rates_up, opt["staffing"], SIM_REPLICATIONS, seed=2)
sim_resolve = simulate_week(rates_up, opt_up["staffing"], SIM_REPLICATIONS, seed=2)
line()
line(f"## 4. Scenario: demand rises {SCENARIO_DEMAND_GROWTH:.0%}")
line(f"| Option | Cost/week | Avg wait (min) | Seen within {WAIT_TARGET_MIN} min |")
line("|---|---|---|---|")
line(f"| Keep current roster | ${opt['cost']:,.0f} | {sim_keep['avg_wait']:.1f} | {sim_keep['pct_within_target']:.0%} |")
line(f"| Re-optimize roster | ${opt_up['cost']:,.0f} | {sim_resolve['avg_wait']:.1f} | {sim_resolve['pct_within_target']:.0%} |")

with open(os.path.join(OUT, "results.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(report) + "\n")

# ---------- Charts ----------
plt.rcParams.update({"figure.dpi": 120, "font.size": 9})

# Chart 1: forecast pattern
fig, ax = plt.subplots(figsize=(7, 3.5))
for d in ["Mon", "Wed", "Sat", "Sun"]:
    s = fc[fc.day == d]
    ax.plot(s.hour, s.forecast, marker="o", label=d)
ax.set(title="Forecast patient arrivals by hour", xlabel="Hour of day", ylabel="Patients per hour")
ax.legend(); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(os.path.join(OUT, "1_forecast.png"))

# Chart 2: staffing vs requirement on Monday
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.bar(HOURS, [required[("Mon", h)] for h in HOURS], color="#cfd8e3", label="Staff required")
ax.step(HOURS, [opt["staffing"][("Mon", h)] for h in HOURS], where="mid", lw=2, label="Optimized schedule")
ax.step(HOURS, [flat["staffing"][("Mon", h)] for h in HOURS], where="mid", lw=2, ls="--", label="Flat (peak-sized)")
ax.step(HOURS, [flat_avg["staffing"][("Mon", h)] for h in HOURS], where="mid", lw=2, ls=":", label="Flat (average-sized)")
ax.set(title="Monday: staff on duty vs. staff required", xlabel="Hour of day", ylabel="Staff")
ax.legend(); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(os.path.join(OUT, "2_monday_staffing.png"))

# Chart 3: average wait by day
fig, ax = plt.subplots(figsize=(7, 3.5))
xs = range(len(DAYS)); w = 0.27
ax.bar([i - w for i in xs], [sim_opt["avg_wait_by_day"][d] for d in DAYS], w, label="Optimized")
ax.bar(list(xs), [sim_flat["avg_wait_by_day"][d] for d in DAYS], w, label="Flat (peak-sized)")
ax.bar([i + w for i in xs], [sim_flat_avg["avg_wait_by_day"][d] for d in DAYS], w, label="Flat (average-sized)")
ax.set_xticks(list(xs)); ax.set_xticklabels(DAYS)
ax.set(title="Simulated average wait by day", ylabel="Minutes")
ax.legend(); ax.grid(alpha=.3, axis="y"); fig.tight_layout(); fig.savefig(os.path.join(OUT, "3_wait_by_day.png"))

print(f"\nAll outputs saved in: {OUT}")
