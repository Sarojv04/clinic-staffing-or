# Clinic Staffing: Forecast → Optimize → Simulate

A small Operational Research project. A walk-in clinic needs to decide how many staff to put on each shift.
Too few staff and patients wait; too many and wages are wasted. The project answers that question in four steps:

1. **Forecast** next week's patient arrivals for every day and hour (seasonal average + trend, tested against a naive forecast).
2. **Optimize** the shift roster with **linear (integer) programming in PuLP**: choose how many 4-, 6- and 8-hour shifts start at each hour so every hour has enough staff, at the lowest wage cost.
3. **Simulate** the clinic with **discrete-event simulation in SimPy**: random patient arrivals, random service times, one queue, staff levels changing hour by hour. Measures waiting times for each roster over 30 simulated weeks.
4. **What-if scenario**: demand rises 20%. Compare keeping the current roster with re-optimizing it.

The patient data is synthetic (generated in `src/data.py`), so there is no real patient information.

## How to run (Windows)

1. Install Python 3.10 or newer from python.org (tick "Add Python to PATH" during install).
2. Open **Command Prompt** in this folder (in File Explorer, click the address bar, type `cmd`, press Enter).
3. Run:
   ```
   pip install -r requirements.txt
   python src\run_all.py
   ```
   Or just double-click **run.bat**, which does both.
4. Results appear on screen and in the `outputs` folder:
   - `results.md`: the summary tables
   - `1_forecast.png`, `2_monday_staffing.png`, `3_wait_by_day.png`: charts
   - `optimized_roster.csv`: the shift plan the optimizer chose
   - `forecast_next_week.csv`, `patient_arrivals_history.csv`: the data

It takes a few seconds to run.

## Results (default settings)

| Schedule | Cost/week | Avg wait (min) | Seen within 15 min |
|---|---|---|---|
| Optimized (PuLP) | $13,930 | 2.7 | 94% |
| Flat, sized to the busiest hour | $16,666 | 1.0 | 98% |
| Flat, sized to the average hour | $11,904 | 8.1 | 80% |

- The optimized roster costs **16% less** than staffing for the peak all day, and still sees 94% of patients within 15 minutes.
- The cheap flat roster saves money but leaves about 1 in 5 patients waiting more than 15 minutes, worst on Monday and Thursday peaks.
- If demand grows 20%, keeping the old roster drops service to 85% within 15 minutes; re-optimizing restores 95% for about $2,700/week more.

## Files

| File | What it does |
|---|---|
| `src/config.py` | All settings: opening hours, service time, wages, shift lengths, scenario size |
| `src/data.py` | Generates 12 weeks of synthetic hourly patient arrivals |
| `src/forecast.py` | Forecast + hold-out backtest (mean absolute error) |
| `src/optimize.py` | PuLP integer program for shift scheduling, plus flat baselines |
| `src/simulate.py` | SimPy discrete-event simulation of the clinic queue |
| `src/run_all.py` | Runs everything, prints results, saves charts |

## The optimization model

- **Decision variable:** `x[day, start, length]` = number of staff who start a shift of that length at that hour (whole numbers).
- **Objective:** minimize total wage cost. Short shifts cost slightly more per hour.
- **Constraint:** for every day and open hour, staff on duty ≥ staff required.
- **Staff required** = forecast patients × 15 min ÷ 60 ÷ 80% target utilization, rounded up.

## Things to try

Change a value in `src/config.py` and run again:
- `SCENARIO_DEMAND_GROWTH = 0.35` to test a bigger demand jump
- `TARGET_UTILIZATION = 0.90` to see cost fall and waits rise (the trade-off)
- Remove the 4-hour shift from `SHIFTS` to see how shift flexibility affects cost
