# 📐 Statistical Sampling Tool

> An interactive tool for understanding the mathematics behind sample size decisions.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red) ![License](https://img.shields.io/badge/license-MIT-green)

---

## What this is

When you cannot check every item in a large set, you check a sample. Statistical sampling gives you a principled way to decide how many items to check — and, after checking them, what you can reasonably conclude about the items you did not.

This tool makes that reasoning visible. Instead of a table that hands you a number, it shows you where the number comes from, how it changes when your assumptions change, and what your results actually mean once testing is complete.

---

## The core ideas, without the jargon

**How large should my sample be?**

Two things drive sample size: how confident you want to be, and how much error you are willing to tolerate. Higher confidence means more items. A tighter tolerance means more items. But there is a third factor most tables ignore — if you already have reason to believe the error rate is low, your required sample is smaller than the table suggests. This tool accounts for all three.

**I tested my sample and found some errors. How bad is it really?**

Finding 1 error in 60 items does not mean the error rate is 1/60 = 1.7%. That is only the point estimate — the centre of a range. The more useful question is: given what I found, what is the *worst plausible* error rate across the full population? At 95% confidence, 1 error in 60 gives an upper bound of 7.66%. That bound is what you should be comparing against your tolerance threshold, not the raw ratio.

**I am testing monetary values, not just pass/fail. How does that work?**

When items have different sizes — some invoices are €500, others are €50,000 — you want larger items to have a higher chance of being selected. This is called probability-proportional-to-size sampling. The mathematics here use the Poisson distribution to model how rare errors behave in large populations, and produce an Upper Error Limit: the maximum total monetary error you can reasonably claim exists, including in the items you never looked at.

---

## Modules

### Module 1 — Attribute Sampling

For populations where each item is either correct or not: a transaction was approved or it wasn't, a record exists or it doesn't.

**What it calculates**
- How many items to test, given your confidence level, tolerance, and prior expectation
- Finite Population Correction: adjusts the sample size downward when the population is small relative to the sample
- Upper Deviation Rate (UDR): the worst plausible error rate in the full population, given what you found — computed using the Clopper-Pearson exact method
- Sampling risk: the probability of drawing the wrong conclusion in either direction

**Key formula**
```
n = Z² × p̂(1 − p̂) / e²

where:
  Z   = one-tailed z-score at the desired confidence level
  p̂   = expected deviation rate (your prior estimate)
  e   = precision gap = tolerable rate − expected rate
```

The precision gap `e` is the part most tables collapse away. If your tolerance is 5% and you expect 2%, you have 3 percentage points of room — and that room is what determines your required sample size, not the 5% alone.

**Visualisations**
- Sensitivity heatmap: how sample size shifts across a grid of confidence levels and tolerance values
- UDR curve: how the upper bound on the error rate grows as more errors are found, with the tolerance threshold shown as a fixed line

---

### Module 2 — Monetary Unit Sampling (MUS)

For populations measured in monetary value, where items vary in size and larger items carry more risk.

**What it calculates**
- Sample size using the Poisson reliability factor: `R₀ = −ln(1 − CL)`
- Sampling interval: the monetary value represented by each selected item
- Upper Error Limit (UEL): the maximum total monetary error in the population, decomposed into three parts:
  - Basic Precision — the minimum uncertainty even with zero errors found
  - Projected Misstatements — the direct projection of found errors onto the full population
  - Incremental Allowance — an additional conservative adjustment for the ranking of error sizes

**Why Poisson?**
Errors in large monetary populations are rare events. The Poisson distribution is the natural model for rare events — it describes how likely it is to observe k occurrences when the underlying rate is low. The reliability factor R₀ at common confidence levels:

| Confidence | R₀     |
|-----------|--------|
| 85%       | 1.897  |
| 90%       | 2.303  |
| 95%       | 2.996  |
| 99%       | 4.605  |

Note that R₀ = −ln(1 − CL). At 95%, that is −ln(0.05) = 2.996. This single number drives both the sample size and the upper error limit.

**Visualisations**
- UEL bar chart: the three components stacked against the tolerable misstatement threshold
- Sample size curve: how n changes continuously as confidence level varies

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/audit-sampling-tool.git
cd audit-sampling-tool

pip install streamlit scipy numpy plotly

python -m streamlit run app.py
```

**Requirements:** Python 3.11+

---

## Project structure

```
audit-sampling-tool/
├── app.py              # Streamlit UI
├── sampling_core.py    # Mathematical engine — no UI dependencies
└── README.md
```

`sampling_core.py` can be used independently:

```python
from sampling_core import attribute_sample_size, mus_sample_size

result = attribute_sample_size(
    confidence_level=0.95,
    tolerable_deviation_rate=0.05,
    expected_deviation_rate=0.02,
    population_size=320,
)
# {'n_infinite': 59, 'n_adjusted': 47, 'z_score': 1.6449, ...}

mus = mus_sample_size(
    population_value=5_000_000,
    tolerable_misstatement=150_000,
    confidence_level=0.95,
)
# {'sample_size': 100, 'sampling_interval': 50083.0, 'reliability_factor': 2.996, ...}
```

---

## Mathematical references

| Concept | Source |
|--------|--------|
| Normal approximation to the Binomial | Standard statistical inference |
| Clopper-Pearson exact confidence interval | Clopper & Pearson (1934), *Biometrika* |
| Poisson reliability factors for MUS | Leslie, Teitlebaum & Anderson (1979) |
| Finite Population Correction | Cochran, *Sampling Techniques* (3rd ed., 1977) |

---

## Author

**Dimitrios** — Applied Mathematics (BSc + MSc)


---

## License

MIT — use freely, attribution appreciated.
