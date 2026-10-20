# Decision memo: new loan landing page

**Decision: Ship the new landing page to 100% of traffic.**

| | Current page | New page | Change (95% CI) |
|---|---:|---:|---|
| Visitor -> application | 4.16% | 4.59% | 10.4% relative (3.6% to 17.2%) |
| Approval rate (guardrail) | 61.4% | 60.9% | -0.4 pts (-3.7 pts to +2.8 pts) |
| Approved applications per 1,000 visitors | 25.5 | 28.0 | |

**Why**
- The test was sized before launch to detect a 10% lift (39,475 visitors per arm) and ran to that size, so the result isn't an early peek.
- More visitors apply, and the whole interval sits above zero.
- Approval rate dipped slightly, but the worst case in the interval (-3.7 pts) stays inside the -5.0 pts limit we agreed before launch. Approved applications per visitor still go up.

**Watch after launch**
- Approval rate weekly for the first month. If it falls more than 5 points below the old page, roll back and investigate who the new page is attracting.
- The true lift is likely nearer the middle of the range than the top. Plan on about 10%, not 17%.
