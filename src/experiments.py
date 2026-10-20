"""Small, readable experiment-analysis helpers: sizing, readouts, multiple
comparisons, CUPED, and sequential monitoring."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


# ---------- sizing ----------

def sample_size_per_arm(base_rate: float, rel_mde: float, alpha: float = 0.05, power: float = 0.80) -> int:
    """Visitors per arm to detect a relative lift `rel_mde` on a conversion rate
    (two-sided test of two proportions)."""
    p1, p2 = base_rate, base_rate * (1 + rel_mde)
    za, zb = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
    pbar = (p1 + p2) / 2
    num = (za * np.sqrt(2 * pbar * (1 - pbar)) + zb * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return int(np.ceil(num / (p2 - p1) ** 2))


def power_at(base_rate: float, rel_lift: float, n_per_arm: int, alpha: float = 0.05) -> float:
    p1, p2 = base_rate, base_rate * (1 + rel_lift)
    se = np.sqrt(p1 * (1 - p1) / n_per_arm + p2 * (1 - p2) / n_per_arm)
    za = stats.norm.ppf(1 - alpha / 2)
    return float(stats.norm.cdf(abs(p2 - p1) / se - za))


# ---------- readouts ----------

@dataclass
class Readout:
    metric: str
    control: float
    treatment: float
    diff: float          # treatment - control (absolute)
    ci_low: float
    ci_high: float
    p_value: float

    @property
    def rel_lift(self) -> float:
        return self.diff / self.control

    @property
    def rel_ci(self) -> tuple[float, float]:
        return self.ci_low / self.control, self.ci_high / self.control


def proportions(metric: str, x_c: int, n_c: int, x_t: int, n_t: int, alpha: float = 0.05) -> Readout:
    """Difference in two conversion rates: z-test (pooled) and Wald interval."""
    pc, pt = x_c / n_c, x_t / n_t
    pool = (x_c + x_t) / (n_c + n_t)
    z = (pt - pc) / np.sqrt(pool * (1 - pool) * (1 / n_c + 1 / n_t))
    se = np.sqrt(pc * (1 - pc) / n_c + pt * (1 - pt) / n_t)
    zc = stats.norm.ppf(1 - alpha / 2)
    return Readout(metric, pc, pt, pt - pc, pt - pc - zc * se, pt - pc + zc * se,
                   float(2 * stats.norm.sf(abs(z))))


def means(metric: str, y_c: np.ndarray, y_t: np.ndarray, alpha: float = 0.05) -> Readout:
    """Difference in means with a normal-approximation interval (fine at these sizes)."""
    d = y_t.mean() - y_c.mean()
    se = np.sqrt(y_c.var(ddof=1) / len(y_c) + y_t.var(ddof=1) / len(y_t))
    zc = stats.norm.ppf(1 - alpha / 2)
    return Readout(metric, y_c.mean(), y_t.mean(), d, d - zc * se, d + zc * se,
                   float(2 * stats.norm.sf(abs(d / se))))


def holm(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """Holm-Bonferroni: which hypotheses can be rejected while keeping the chance
    of any false win across all comparisons at `alpha`."""
    order = np.argsort(p_values)
    reject = [False] * len(p_values)
    m = len(p_values)
    for rank, i in enumerate(order):
        if p_values[i] <= alpha / (m - rank):
            reject[i] = True
        else:
            break
    return reject


def holm_adjusted(p_values: list[float]) -> list[float]:
    """Holm-adjusted p-values (comparable directly to alpha)."""
    m = len(p_values)
    order = np.argsort(p_values)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p_values[i])
        adj[i] = min(1.0, running)
    return adj.tolist()


# ---------- CUPED ----------

def cuped(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, float]:
    """Adjust outcome y using pre-experiment covariate x. Because x was measured
    before randomisation, the adjustment removes noise without biasing the effect."""
    theta = np.cov(x, y, ddof=1)[0, 1] / x.var(ddof=1)
    return y - theta * (x - x.mean()), float(theta)


# ---------- sequential monitoring ----------

def cumulative_z(a: np.ndarray, b: np.ndarray, daily_n: int) -> np.ndarray:
    """z-statistic after each day for many A/A tests (rows = tests, cols = days)."""
    ca, cb = a.cumsum(axis=1), b.cumsum(axis=1)
    n = daily_n * np.arange(1, a.shape[1] + 1)
    pa, pb = ca / n, cb / n
    pool = (ca + cb) / (2 * n)
    return (pb - pa) / np.sqrt(pool * (1 - pool) * 2 / n)


def obf_boundaries(n_looks: int, alpha: float = 0.05, n_sims: int = 200_000, seed: int = 0) -> np.ndarray:
    """O'Brien-Fleming-style boundaries for equally spaced looks: z_k = c * sqrt(K / k),
    with c set by simulation so the overall false-positive rate is `alpha`.
    Early looks need very strong evidence; the final look is close to the usual 1.96."""
    rng = np.random.default_rng(seed)
    steps = rng.standard_normal((n_sims, n_looks))
    z = steps.cumsum(axis=1) / np.sqrt(np.arange(1, n_looks + 1))
    shape = np.sqrt(n_looks / np.arange(1, n_looks + 1))
    c = np.quantile((np.abs(z) / shape).max(axis=1), 1 - alpha)
    return c * shape
