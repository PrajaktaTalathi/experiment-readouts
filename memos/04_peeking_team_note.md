# Team note: why we don't stop tests early

In 4,000 simulated A/A tests (identical experiences, so any "win" is false):

| How results were checked | False wins |
|---|---:|
| Once, at the planned end | 4.8% |
| Every day, stopping at the first p < 0.05 | 27.4% |
| Once a week, with O'Brien-Fleming thresholds | 5.0% |

**Rule going forward**
- Size every test before launch and say when it ends.
- Dashboards can show results daily, but only the planned look decides.
- If a test needs early stopping (e.g. something is clearly broken), plan weekly looks with stricter early thresholds: z above 4.05 in week 1, 2.86 in week 2, 2.34 in week 3 and 2.02 at the end.
