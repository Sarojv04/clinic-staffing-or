# Clinic Staffing: Forecast -> Optimize -> Simulate

History: 12 weeks, 11,906 synthetic patient arrivals

## 1. Forecast (hold-out test on the last week, mean absolute error, patients/hour)
- Seasonal average + trend: 3.38
- Naive (last week): 4.25
- Forecast for next week: 1032 patients

## 2. Optimization (PuLP integer program)
- Solver status: Optimal
- Optimized schedule: $13,930/week, 410 paid staff-hours
- Flat schedule sized to the peak hour: $16,666/week, 504 paid staff-hours
- Flat schedule sized to the average hour: $11,904/week, 360 paid staff-hours
- Saving vs. peak-sized flat schedule: $2,736/week (16%)

## 3. Simulation (SimPy, 30 simulated weeks each)
| Schedule | Cost/week | Avg wait (min) | 90th pct wait (min) | Seen within 15 min |
|---|---|---|---|---|
| Optimized (PuLP) | $13,930 | 2.7 | 9.8 | 94% |
| Flat - peak-sized | $16,666 | 1.0 | 2.7 | 98% |
| Flat - average-sized | $11,904 | 8.1 | 26.5 | 80% |

## 4. Scenario: demand rises 20%
| Option | Cost/week | Avg wait (min) | Seen within 15 min |
|---|---|---|---|
| Keep current roster | $13,930 | 6.1 | 85% |
| Re-optimize roster | $16,637 | 2.4 | 95% |
