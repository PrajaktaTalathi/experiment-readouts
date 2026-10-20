# Decision memo: simpler document upload for returning customers

**Decision: Ship the new upload step for returning customers.**

| Method | Change in days to complete (95% CI) | p-value |
|---|---|---:|
| Standard comparison | -0.34 (-0.74 to +0.06) | 0.097 |
| CUPED (adjusted for last year's time) | -0.43 (-0.64 to -0.22) | 0.00008 |

**Why**
- Returning customers are a small segment (800 per arm), so the standard comparison is inconclusive.
- How long a customer took last year predicts how long they take this year. Adjusting for it (CUPED) removes 71% of the noise. Because it was measured before the test, it can't bias the result.
- With the adjustment, the new step saves about 0.4 days per application, and the whole interval is below zero. Getting the same precision without CUPED would have needed about 2,818 customers per arm.

**Next**
- Make CUPED the default for any test on returning customers, and decide the covariate before launch, not after.
