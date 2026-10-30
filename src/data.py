"""Step 1 - Create synthetic patient-arrival history for a walk-in clinic.

The data is made up (no real patients). It has realistic patterns:
a Monday peak, a quieter weekend, a morning rush and an after-work rush.
"""
import numpy as np
import pandas as pd

from config import DAYS, HOURS, WEEKS_OF_HISTORY, RANDOM_SEED

DAY_FACTOR = {"Mon": 1.30, "Tue": 1.10, "Wed": 1.00, "Thu": 1.05, "Fri": 1.15, "Sat": 0.80, "Sun": 0.60}
HOUR_FACTOR = {8: 1.4, 9: 1.6, 10: 1.3, 11: 1.0, 12: 0.9, 13: 0.8,
               14: 0.8, 15: 0.9, 16: 1.1, 17: 1.5, 18: 1.6, 19: 1.1}
BASE_ARRIVALS_PER_HOUR = 10.0


def true_rate(day, hour, week=0):
    trend = 1 + 0.005 * week  # slow growth of 0.5% per week
    return BASE_ARRIVALS_PER_HOUR * DAY_FACTOR[day] * HOUR_FACTOR[hour] * trend


def make_history(weeks=WEEKS_OF_HISTORY, seed=RANDOM_SEED):
    rng = np.random.default_rng(seed)
    rows = []
    for w in range(weeks):
        for d in DAYS:
            for h in HOURS:
                rows.append({"week": w + 1, "day": d, "hour": h,
                             "arrivals": int(rng.poisson(true_rate(d, h, w)))})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = make_history()
    print(df.head(12))
    print("Total patients in history:", df.arrivals.sum())
