"""Step 3 - Choose the cheapest shift schedule with linear (integer) programming in PuLP.

Decision variables
    x[day, start, length] = number of staff starting a shift of `length` hours at `start`

Objective
    minimise total wage cost = sum(x * shift cost)

Constraints
    for every day and open hour: staff on duty >= staff required in that hour
    shifts must start and end inside opening hours
"""
import math
import pulp

from config import (DAYS, HOURS, OPEN_HOUR, CLOSE_HOUR, SHIFTS, SERVICE_MIN,
                    TARGET_UTILIZATION, MIN_STAFF)


def staff_required(forecast_df):
    """Convert forecast patients per hour into staff needed per hour.
    Workload (staff-hours) = patients * service minutes / 60; divide by target utilization."""
    req = {}
    for r in forecast_df.itertuples():
        load = r.forecast * SERVICE_MIN / 60
        req[(r.day, r.hour)] = max(MIN_STAFF, math.ceil(load / TARGET_UTILIZATION))
    return req


def possible_shifts():
    return [(start, length) for length in SHIFTS
            for start in range(OPEN_HOUR, CLOSE_HOUR - length + 1)]


def solve_schedule(required):
    shifts = possible_shifts()
    prob = pulp.LpProblem("clinic_shift_scheduling", pulp.LpMinimize)
    x = {(d, s, L): pulp.LpVariable(f"x_{d}_{s}_{L}", lowBound=0, cat="Integer")
         for d in DAYS for (s, L) in shifts}

    prob += pulp.lpSum(x[d, s, L] * SHIFTS[L] for (d, s, L) in x), "total_wage_cost"

    for d in DAYS:
        for h in HOURS:
            on_duty = pulp.lpSum(x[d, s, L] for (s, L) in shifts if s <= h < s + L)
            prob += on_duty >= required[(d, h)], f"cover_{d}_{h}"

    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[prob.status]

    roster = [{"day": d, "start": s, "end": s + L, "length": L, "staff": int(round(v.value()))}
              for (d, s, L), v in x.items() if v.value() and v.value() > 0.5]
    staffing = {(d, h): sum(r["staff"] for r in roster if r["day"] == d and r["start"] <= h < r["end"])
                for d in DAYS for h in HOURS}
    return {"status": status, "cost": pulp.value(prob.objective), "roster": roster,
            "staffing": staffing, "paid_hours": sum(r["staff"] * r["length"] for r in roster)}


def flat_schedule(required, mode="peak"):
    """Rule-of-thumb baselines: the same headcount all day (an 8h + a 4h shift per person-slot).
    mode="peak":    headcount = the day's busiest hour (safe but expensive)
    mode="average": headcount = the day's average need (cheap but short at peak times)"""
    staffing, cost, hours = {}, 0.0, 0
    for d in DAYS:
        needs = [required[(d, h)] for h in HOURS]
        level = max(needs) if mode == "peak" else max(MIN_STAFF, round(sum(needs) / len(needs)))
        for h in HOURS:
            staffing[(d, h)] = level
        cost += level * (SHIFTS[8] + SHIFTS[4])  # 8h + 4h shift covers the 12h day
        hours += level * 12
    return {"status": "Rule of thumb", "cost": cost, "staffing": staffing, "paid_hours": hours}
