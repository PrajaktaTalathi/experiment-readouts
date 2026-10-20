"""Synthetic user-level data for four acquisition experiments.

1. Landing page: a redesigned loan landing page vs the current one.
   Primary metric: visitor -> application rate. Guardrail: approval rate of
   those applications (more applications are no good if they're lower quality).
2. Email subject lines: control plus three new subject lines, one test.
   Metric: email -> application rate.
3. Returning-customer journey: a simpler document-upload step.
   Metric: days to complete an application (lower is better). Each customer's
   days-to-complete last year is known, which CUPED uses to cut noise.
4. A/A tests (no real difference) checked every day, to show what peeking does.

All numbers here are synthetic. No real company data is used.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# 1. Landing page
LP_N = 40_000                 # visitors per arm (sized in run_analysis.py for a 10% lift)
LP_RATE = (0.040, 0.0446)     # true application rate: control, new page (~11.5% lift)
LP_APPROVAL = (0.620, 0.612)  # true approval rate of applications (small, harmless dip)

# 2. Email subject lines
EMAIL_N = 15_000              # recipients per arm
EMAIL_ARMS = ["Control", "Rate-led", "Deadline-led", "Social proof"]
EMAIL_RATE = [0.0200, 0.0210, 0.0236, 0.0204]

# 3. Returning-customer journey (CUPED)
JOURNEY_N = 800               # returning customers per arm (a small segment)
JOURNEY_DAYS = 9.0            # average days to complete an application
JOURNEY_EFFECT = -0.45        # new upload step saves ~half a day on average

# 4. Peeking
AA_DAYS = 28
AA_DAILY_N = 1_000            # visitors per arm per day
AA_RATE = 0.04


def landing_page(seed: int = 18) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    frames = []
    for arm, rate, appr in zip(["control", "treatment"], LP_RATE, LP_APPROVAL):
        applied = rng.random(LP_N) < rate
        approved = np.where(applied, rng.random(LP_N) < appr, np.nan)
        frames.append(pd.DataFrame({"arm": arm, "applied": applied.astype(int), "approved": approved}))
    return pd.concat(frames, ignore_index=True)


def email(seed: int = 47) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    frames = [pd.DataFrame({"arm": arm, "applied": (rng.random(EMAIL_N) < rate).astype(int)})
              for arm, rate in zip(EMAIL_ARMS, EMAIL_RATE)]
    return pd.concat(frames, ignore_index=True)


def journey(seed: int = 8) -> pd.DataFrame:
    """Days to complete depends mostly on the customer (some are always quick,
    some always slow), which is why last year's value predicts this year's."""
    rng = np.random.default_rng(seed)
    n = 2 * JOURNEY_N
    customer_speed = rng.gamma(shape=6, scale=JOURNEY_DAYS / 6, size=n)
    last_year = np.clip(customer_speed + rng.normal(0, 1.6, n), 0.5, None)
    treat = np.r_[np.zeros(JOURNEY_N), np.ones(JOURNEY_N)].astype(int)
    this_year = np.clip(customer_speed + rng.normal(0, 1.6, n) + JOURNEY_EFFECT * treat, 0.5, None)
    return pd.DataFrame({
        "arm": np.where(treat == 1, "treatment", "control"),
        "days_last_year": last_year.round(2),
        "days_to_complete": this_year.round(2),
    })


def aa_daily_counts(n_sims: int = 4_000, seed: int = 13) -> tuple[np.ndarray, np.ndarray]:
    """Daily conversions for many A/A tests: arrays of shape (n_sims, days) per arm."""
    rng = np.random.default_rng(seed)
    a = rng.binomial(AA_DAILY_N, AA_RATE, size=(n_sims, AA_DAYS))
    b = rng.binomial(AA_DAILY_N, AA_RATE, size=(n_sims, AA_DAYS))
    return a, b
