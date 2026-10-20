"""End-to-end readouts for four synthetic acquisition experiments.

Run:  python run_analysis.py
Writes data to ./data, charts and readout.txt to ./charts, and one decision
memo per test to ./memos. Takes a few seconds.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src import experiments as ex
from src import simulate as sim

ALPHA = 0.05
for d in ("data", "charts", "memos"):
    Path(d).mkdir(exist_ok=True)

# =====================================================================
# 1. Landing page: size it, run it, read primary + guardrail
# =====================================================================
BASE, MDE = sim.LP_RATE[0], 0.10
n_needed = ex.sample_size_per_arm(BASE, MDE)
lp = sim.landing_page()
lp.to_csv("data/landing_page.csv", index=False)
g = lp.groupby("arm").applied.agg(["sum", "count"])
lp_primary = ex.proportions("Visitor -> application rate", g.loc["control", "sum"], g.loc["control", "count"],
                            g.loc["treatment", "sum"], g.loc["treatment", "count"])
apps = lp[lp.applied == 1].groupby("arm").approved.agg(["sum", "count"])
lp_guard = ex.proportions("Approval rate (guardrail)", int(apps.loc["control", "sum"]), apps.loc["control", "count"],
                          int(apps.loc["treatment", "sum"]), apps.loc["treatment", "count"])
GUARD_LIMIT = -0.05  # we agreed up front we'd accept at most a 5-point drop in approval rate
guard_ok = lp_guard.ci_low > GUARD_LIMIT
approved_per_1k = {arm: 1000 * apps.loc[arm, "sum"] / g.loc[arm, "count"] for arm in ("control", "treatment")}

# =====================================================================
# 2. Email subject lines: three comparisons, so correct for multiple tests
# =====================================================================
em = sim.email()
em.to_csv("data/email_subject_lines.csv", index=False)
ge = em.groupby("arm").applied.agg(["sum", "count"])
email_reads = [ex.proportions(arm, ge.loc["Control", "sum"], ge.loc["Control", "count"],
                              ge.loc[arm, "sum"], ge.loc[arm, "count"]) for arm in sim.EMAIL_ARMS[1:]]
raw_p = [r.p_value for r in email_reads]
holm_p = ex.holm_adjusted(raw_p)
naive_winners = [r.metric for r, p in zip(email_reads, raw_p) if p < ALPHA and r.diff > 0]
holm_winners = [r.metric for r, p in zip(email_reads, holm_p) if p < ALPHA and r.diff > 0]

# =====================================================================
# 3. Returning-customer journey: raw vs CUPED
# =====================================================================
jr = sim.journey()
jr.to_csv("data/journey_returning_customers.csv", index=False)
t = (jr.arm == "treatment").values
y, x = jr.days_to_complete.values, jr.days_last_year.values
j_raw = ex.means("Days to complete (raw)", y[~t], y[t])
y_adj, theta = ex.cuped(y, x)
j_cuped = ex.means("Days to complete (CUPED)", y_adj[~t], y_adj[t])
var_cut = 1 - y_adj.var() / y.var()
width_raw, width_cuped = j_raw.ci_high - j_raw.ci_low, j_cuped.ci_high - j_cuped.ci_low
equiv_n = int(round(sim.JOURNEY_N * (width_raw / width_cuped) ** 2))

# =====================================================================
# 4. Peeking: A/A tests checked every day vs a planned sequential design
# =====================================================================
a, b = sim.aa_daily_counts()
z = ex.cumulative_z(a, b, sim.AA_DAILY_N)
fp_fixed = float((np.abs(z[:, -1]) > 1.96).mean())
fp_daily = float((np.abs(z) > 1.96).any(axis=1).mean())
looks = np.array([6, 13, 20, 27])          # end of each week
bounds = ex.obf_boundaries(len(looks))
fp_obf = float((np.abs(z[:, looks]) > bounds).any(axis=1).mean())
fp_by_day = [(np.abs(z[:, :d]) > 1.96).any(axis=1).mean() for d in range(1, sim.AA_DAYS + 1)]

# =====================================================================
# Readout
# =====================================================================
def pct(v, d=1):
    return f"{v * 100:.{d}f}%"

def pts(v):
    return f"{v * 100:+.1f} pts"

lines = [
    "EXPERIMENT READOUTS (synthetic data)",
    "",
    "1. LANDING PAGE",
    f"   Sizing: to detect a {pct(MDE, 0)} relative lift on a {pct(BASE)} base with 80% power -> "
    f"{n_needed:,} visitors per arm. Ran {sim.LP_N:,} per arm.",
    f"   Applications: {pct(lp_primary.control, 2)} -> {pct(lp_primary.treatment, 2)}, "
    f"lift {pct(lp_primary.rel_lift)} (95% CI {pct(lp_primary.rel_ci[0])} to {pct(lp_primary.rel_ci[1])}), "
    f"p = {lp_primary.p_value:.4f}",
    f"   Guardrail, approval rate: {pct(lp_guard.control)} -> {pct(lp_guard.treatment)}, "
    f"{pts(lp_guard.diff)} (95% CI {pts(lp_guard.ci_low)} to {pts(lp_guard.ci_high)}); "
    f"agreed limit {pts(GUARD_LIMIT)} -> {'within limit' if guard_ok else 'BREACHED'}",
    f"   Approved applications per 1,000 visitors: {approved_per_1k['control']:.1f} -> {approved_per_1k['treatment']:.1f}",
    "",
    "2. EMAIL SUBJECT LINES (three new lines vs control)",
]
for r, p, hp in zip(email_reads, raw_p, holm_p):
    lines.append(f"   {r.metric:<14} {pct(r.control, 2)} -> {pct(r.treatment, 2)}  lift {pct(r.rel_lift):>6}  "
                 f"p = {p:.4f}  Holm-adjusted p = {hp:.4f}")
lines += [
    f"   Winners if each is tested alone: {', '.join(naive_winners) or 'none'}",
    f"   Winners after correcting for three comparisons: {', '.join(holm_winners) or 'none'}",
    "",
    f"3. RETURNING-CUSTOMER JOURNEY ({sim.JOURNEY_N:,} customers per arm)",
    f"   Raw:   {j_raw.diff:+.2f} days (95% CI {j_raw.ci_low:+.2f} to {j_raw.ci_high:+.2f}), p = {j_raw.p_value:.3f}",
    f"   CUPED: {j_cuped.diff:+.2f} days (95% CI {j_cuped.ci_low:+.2f} to {j_cuped.ci_high:+.2f}), p = {j_cuped.p_value:.5f}",
    f"   Last year's days-to-complete removed {pct(var_cut, 0)} of the noise (theta = {theta:.2f}); "
    f"the interval is {pct(1 - width_cuped / width_raw, 0)} narrower, worth about {equiv_n:,} customers per arm "
    f"without CUPED.",
    "",
    f"4. PEEKING ({len(z):,} A/A tests, {sim.AA_DAYS} days, no real difference)",
    f"   Check once at the end:                 {pct(fp_fixed)} false wins",
    f"   Check every day, stop at first p<0.05:  {pct(fp_daily)} false wins",
    f"   Planned weekly looks, O'Brien-Fleming:  {pct(fp_obf)} false wins "
    f"(z thresholds {', '.join(f'{v:.2f}' for v in bounds)})",
]
readout = "\n".join(lines)
print(readout)
Path("charts/readout.txt").write_text(readout)

# =====================================================================
# Decision memos
# =====================================================================
lp_decision = "Ship" if (lp_primary.ci_low > 0 and guard_ok) else ("Hold" if not guard_ok else "Extend")
memo_lp = f"""# Decision memo: new loan landing page

**Decision: {lp_decision} the new landing page to 100% of traffic.**

| | Current page | New page | Change (95% CI) |
|---|---:|---:|---|
| Visitor -> application | {pct(lp_primary.control, 2)} | {pct(lp_primary.treatment, 2)} | {pct(lp_primary.rel_lift)} relative ({pct(lp_primary.rel_ci[0])} to {pct(lp_primary.rel_ci[1])}) |
| Approval rate (guardrail) | {pct(lp_guard.control)} | {pct(lp_guard.treatment)} | {pts(lp_guard.diff)} ({pts(lp_guard.ci_low)} to {pts(lp_guard.ci_high)}) |
| Approved applications per 1,000 visitors | {approved_per_1k['control']:.1f} | {approved_per_1k['treatment']:.1f} | |

**Why**
- The test was sized before launch to detect a {pct(MDE, 0)} lift ({n_needed:,} visitors per arm) and ran to that size, so the result isn't an early peek.
- More visitors apply, and the whole interval sits above zero.
- Approval rate dipped slightly, but the worst case in the interval ({pts(lp_guard.ci_low)}) stays inside the {pts(GUARD_LIMIT)} limit we agreed before launch. Approved applications per visitor still go up.

**Watch after launch**
- Approval rate weekly for the first month. If it falls more than 5 points below the old page, roll back and investigate who the new page is attracting.
- The true lift is likely nearer the middle of the range than the top. Plan on about {pct(lp_primary.rel_lift, 0)}, not {pct(lp_primary.rel_ci[1], 0)}.
"""

best = max(zip(email_reads, holm_p), key=lambda rp: rp[0].diff)[0]
memo_email = f"""# Decision memo: email subject lines

**Decision: Roll out "{best.metric}" as the new default subject line. Don't switch to any other line yet.**

| Subject line | Application rate | Lift vs control | p (alone) | p (corrected for 3 tests) |
|---|---:|---:|---:|---:|
| Control | {pct(email_reads[0].control, 2)} | | | |
""" + "\n".join(
    f"| {r.metric} | {pct(r.treatment, 2)} | {pct(r.rel_lift)} | {p:.4f} | {hp:.4f} |"
    for r, p, hp in zip(email_reads, raw_p, holm_p)) + f"""

**Why**
- Testing three new lines at once gives three chances to find a "winner" by luck. The corrected p-values (Holm) keep the overall chance of a false win at 5%.
- "{best.metric}" wins clearly either way.
- {', '.join(set(naive_winners) - set(holm_winners)) or 'No other line'} looks like a winner on its own but doesn't hold up after the correction. Its lift may be real but small; this test can't confirm it.

**Next**
- If a small lift on the runner-up still matters, retest it head-to-head against the new default with a sample sized for that smaller effect.
"""

memo_journey = f"""# Decision memo: simpler document upload for returning customers

**Decision: Ship the new upload step for returning customers.**

| Method | Change in days to complete (95% CI) | p-value |
|---|---|---:|
| Standard comparison | {j_raw.diff:+.2f} ({j_raw.ci_low:+.2f} to {j_raw.ci_high:+.2f}) | {j_raw.p_value:.3f} |
| CUPED (adjusted for last year's time) | {j_cuped.diff:+.2f} ({j_cuped.ci_low:+.2f} to {j_cuped.ci_high:+.2f}) | {j_cuped.p_value:.5f} |

**Why**
- Returning customers are a small segment ({sim.JOURNEY_N:,} per arm), so the standard comparison is inconclusive.
- How long a customer took last year predicts how long they take this year. Adjusting for it (CUPED) removes {pct(var_cut, 0)} of the noise. Because it was measured before the test, it can't bias the result.
- With the adjustment, the new step saves about {abs(j_cuped.diff):.1f} days per application, and the whole interval is below zero. Getting the same precision without CUPED would have needed about {equiv_n:,} customers per arm.

**Next**
- Make CUPED the default for any test on returning customers, and decide the covariate before launch, not after.
"""

memo_peeking = f"""# Team note: why we don't stop tests early

In {len(z):,} simulated A/A tests (identical experiences, so any "win" is false):

| How results were checked | False wins |
|---|---:|
| Once, at the planned end | {pct(fp_fixed)} |
| Every day, stopping at the first p < 0.05 | {pct(fp_daily)} |
| Once a week, with O'Brien-Fleming thresholds | {pct(fp_obf)} |

**Rule going forward**
- Size every test before launch and say when it ends.
- Dashboards can show results daily, but only the planned look decides.
- If a test needs early stopping (e.g. something is clearly broken), plan weekly looks with stricter early thresholds: z above {bounds[0]:.2f} in week 1, {bounds[1]:.2f} in week 2, {bounds[2]:.2f} in week 3 and {bounds[3]:.2f} at the end.
"""
for name, text in (("01_landing_page", memo_lp), ("02_email_subject_lines", memo_email),
                   ("03_returning_customer_upload", memo_journey), ("04_peeking_team_note", memo_peeking)):
    Path(f"memos/{name}.md").write_text(text)

# =====================================================================
# Charts
# =====================================================================
INK, MUTED, ACCENT, SHADE, BLUE = "#1f2a37", "#8a94a3", "#c2410c", "#f1e7df", "#2f5d8a"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})

# 1. Sample size vs MDE
mdes = np.linspace(0.04, 0.25, 50)
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.plot(mdes * 100, [ex.sample_size_per_arm(BASE, m) / 1000 for m in mdes], color=INK, lw=2)
ax.scatter([MDE * 100], [n_needed / 1000], color=ACCENT, zorder=5, s=50)
ax.annotate(f"10% lift -> {n_needed / 1000:.0f}k per arm", (MDE * 100, n_needed / 1000),
            xytext=(12, 50), textcoords="offset points", color=ACCENT)
ax.set_xlabel("Smallest lift worth detecting (relative, %)")
ax.set_ylabel("Visitors needed per arm (k)")
ax.set_title("Halving the lift you want to detect roughly quadruples the sample", loc="left", color=INK)
fig.tight_layout(); fig.savefig("charts/sample_size.png", dpi=150); plt.close(fig)

# 2. Landing page primary + guardrail
fig, axes = plt.subplots(1, 2, figsize=(10, 2.6))
for ax, r, lim, title, scale, unit in (
        (axes[0], lp_primary, None, "Applications: relative lift", 1 / lp_primary.control, "%"),
        (axes[1], lp_guard, GUARD_LIMIT, "Approval rate (guardrail): change", 1, " pts")):
    lo, hi, mid = r.ci_low * scale * 100, r.ci_high * scale * 100, r.diff * scale * 100
    ax.errorbar([mid], [0], xerr=[[mid - lo], [hi - mid]], fmt="o", color=ACCENT, ms=9, capsize=5, lw=2)
    ax.axvline(0, color=INK, lw=0.8)
    if lim is not None:
        ax.axvspan(lim * 100 - 3, lim * 100, color=SHADE, zorder=0)
        ax.axvline(lim * 100, color=MUTED, ls="--", lw=1)
        ax.text(lim * 100, 0.35, " agreed limit", color=MUTED, fontsize=8, va="bottom")
    ax.set_yticks([]); ax.set_ylim(-0.6, 0.6)
    ax.set_xlabel(f"95% interval ({unit.strip()})")
    ax.set_title(title, loc="left", color=INK, fontsize=10)
fig.suptitle("Landing page: more applications, and approval quality stays inside the limit",
             x=0.01, ha="left", color=INK)
fig.tight_layout(); fig.savefig("charts/landing_page.png", dpi=150); plt.close(fig)

# 3. Email arms
fig, ax = plt.subplots(figsize=(8, 3.2))
yy = np.arange(len(email_reads))
for i, (r, hp) in enumerate(zip(email_reads, holm_p)):
    lo, hi = r.rel_ci
    col = ACCENT if hp < ALPHA else MUTED
    ax.errorbar([r.rel_lift * 100], [i], xerr=[[(r.rel_lift - lo) * 100], [(hi - r.rel_lift) * 100]],
                fmt="o", color=col, ms=8, capsize=4, lw=2)
    ax.text(hi * 100 + 1, i, f"p = {raw_p[i]:.3f}  ->  corrected {hp:.3f}", va="center", fontsize=8.5, color=col)
ax.axvline(0, color=INK, lw=0.8)
ax.set_yticks(yy, [r.metric for r in email_reads]); ax.invert_yaxis()
ax.set_xlabel("Lift in application rate vs control (%, 95% interval)")
ax.set_xlim(None, max(r.rel_ci[1] for r in email_reads) * 100 + 30)
ax.set_title("Three subject lines tested: only one clears the corrected bar", loc="left", color=INK)
fig.tight_layout(); fig.savefig("charts/email_subject_lines.png", dpi=150); plt.close(fig)

# 4. CUPED
fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), gridspec_kw={"width_ratios": [1, 1.2]})
ax = axes[0]
ax.scatter(x[~t], y[~t], s=6, color=MUTED, alpha=0.5, label="Control")
ax.scatter(x[t], y[t], s=6, color=BLUE, alpha=0.5, label="New upload step")
ax.set_xlabel("Days to complete, last year"); ax.set_ylabel("Days to complete, this test")
ax.set_title(f"Last year predicts this year ({pct(var_cut, 0)} of noise)", loc="left", color=INK, fontsize=10)
ax.legend(frameon=False, fontsize=8, markerscale=3)
ax = axes[1]
for i, (r, col) in enumerate(((j_raw, MUTED), (j_cuped, ACCENT))):
    ax.errorbar([r.diff], [i], xerr=[[r.diff - r.ci_low], [r.ci_high - r.diff]], fmt="o", color=col, ms=9, capsize=5, lw=2)
    ax.text(r.ci_high + 0.05, i, f"p = {r.p_value:.3f}" if r.p_value >= 0.001 else "p < 0.001", va="center", color=col, fontsize=9)
ax.axvline(0, color=INK, lw=0.8)
ax.set_yticks([0, 1], ["Standard", "CUPED"]); ax.invert_yaxis(); ax.set_ylim(1.6, -0.6)
ax.set_xlabel("Change in days to complete (95% interval)")
ax.set_title("Same data, much tighter answer", loc="left", color=INK, fontsize=10)
fig.tight_layout(); fig.savefig("charts/cuped.png", dpi=150); plt.close(fig)

# 5. Peeking
fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), gridspec_kw={"width_ratios": [1.3, 1]})
ax = axes[0]
days = np.arange(1, sim.AA_DAYS + 1)
ax.plot(days, np.array(fp_by_day) * 100, color=ACCENT, lw=2, label="Peeking every day")
ax.axhline(5, color=INK, ls="--", lw=1, label="Promised 5%")
ax.set_xlabel("Days the test has run"); ax.set_ylabel("Tests declared a 'win' (%)")
ax.set_title("Checking daily quietly inflates false wins", loc="left", color=INK, fontsize=10)
ax.legend(frameon=False, fontsize=8)
ax = axes[1]
labels = ["Check once\nat the end", "Peek daily", "Weekly looks,\nO'Brien-Fleming"]
vals = [fp_fixed * 100, fp_daily * 100, fp_obf * 100]
bars = ax.bar(labels, vals, color=[MUTED, ACCENT, BLUE], width=0.6)
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width() / 2, v + 0.6, f"{v:.1f}%", ha="center", color=INK)
ax.set_ylabel("False wins (%)"); ax.set_ylim(0, max(vals) * 1.2)
ax.tick_params(axis="x", labelsize=8.5)
ax.set_title("A planned design fixes it", loc="left", color=INK, fontsize=10)
fig.tight_layout(); fig.savefig("charts/peeking.png", dpi=150); plt.close(fig)

print("\ncharts written to ./charts, memos written to ./memos")
