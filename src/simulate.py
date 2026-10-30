"""Step 4 - Discrete-event simulation of the clinic in SimPy.

Patients arrive at random (Poisson process with the hour's rate), wait in one queue,
and are seen by the next free staff member (service time is random, exponential).
Staff numbers change hour by hour following the schedule being tested.
We run many simulated weeks and measure waiting times.
"""
import random
import statistics
import simpy

from config import DAYS, HOURS, OPEN_HOUR, CLOSE_HOUR, SERVICE_MIN, WAIT_TARGET_MIN


def _simulate_day(env_seed, rates, staffing_by_hour):
    rnd = random.Random(env_seed)
    env = simpy.Environment()
    max_staff = max(staffing_by_hour.values())
    staff = simpy.PriorityResource(env, capacity=max_staff)
    waits = []

    # A staff "slot" k is off duty in hour h when k >= staff on duty in that hour.
    # Off-duty slots are held by a high-priority placeholder, so patients cannot use them.
    def slot_controller(k):
        held = None
        for h in HOURS:
            off = k >= staffing_by_hour[h]
            if off and held is None:
                held = staff.request(priority=-1)
                yield held
            elif not off and held is not None:
                staff.release(held)
                held = None
            next_change = (h + 1 - OPEN_HOUR) * 60
            if env.now < next_change:
                yield env.timeout(next_change - env.now)
        if held is not None:
            staff.release(held)

    def patient():
        arrived = env.now
        with staff.request(priority=1) as req:
            yield req
            waits.append(env.now - arrived)
            yield env.timeout(rnd.expovariate(1 / SERVICE_MIN))

    def arrivals():
        for h in HOURS:
            end = (h + 1 - OPEN_HOUR) * 60
            rate_per_min = rates[h] / 60
            while True:
                gap = rnd.expovariate(rate_per_min) if rate_per_min > 0 else float("inf")
                if env.now + gap >= end:
                    yield env.timeout(end - env.now)
                    break
                yield env.timeout(gap)
                env.process(patient())

    for k in range(max_staff):
        env.process(slot_controller(k))
    env.process(arrivals())
    # doors close at CLOSE_HOUR; staff on the last shift finish the patients already waiting
    env.run(until=(CLOSE_HOUR - OPEN_HOUR) * 60 + 240)
    return waits


def simulate_week(rate_table, staffing, replications=30, seed=0):
    """rate_table[(day, hour)] = expected arrivals per hour; staffing[(day, hour)] = staff on duty."""
    all_waits, per_day = [], {d: [] for d in DAYS}
    for rep in range(replications):
        for i, d in enumerate(DAYS):
            w = _simulate_day(seed * 100000 + rep * 10 + i,
                              {h: rate_table[(d, h)] for h in HOURS},
                              {h: staffing[(d, h)] for h in HOURS})
            all_waits += w
            per_day[d] += w
    within = sum(1 for w in all_waits if w <= WAIT_TARGET_MIN) / len(all_waits)
    return {
        "avg_wait": statistics.mean(all_waits),
        "p90_wait": statistics.quantiles(all_waits, n=10)[-1],
        "pct_within_target": within,
        "avg_wait_by_day": {d: statistics.mean(v) for d, v in per_day.items()},
        "patients_per_week": len(all_waits) / replications,
    }
