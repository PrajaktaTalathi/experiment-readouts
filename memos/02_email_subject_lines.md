# Decision memo: email subject lines

**Decision: Roll out "Deadline-led" as the new default subject line. Don't switch to any other line yet.**

| Subject line | Application rate | Lift vs control | p (alone) | p (corrected for 3 tests) |
|---|---:|---:|---:|---:|
| Control | 1.85% | | | |
| Rate-led | 2.21% | 19.1% | 0.0300 | 0.0600 |
| Deadline-led | 2.36% | 27.3% | 0.0022 | 0.0067 |
| Social proof | 2.02% | 9.0% | 0.2949 | 0.2949 |

**Why**
- Testing three new lines at once gives three chances to find a "winner" by luck. The corrected p-values (Holm) keep the overall chance of a false win at 5%.
- "Deadline-led" wins clearly either way.
- Rate-led looks like a winner on its own but doesn't hold up after the correction. Its lift may be real but small; this test can't confirm it.

**Next**
- If a small lift on the runner-up still matters, retest it head-to-head against the new default with a sample sized for that smaller effect.
