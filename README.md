# 📐 Audit Sampling Tool

> Statistical sampling for IT audit — where Applied Mathematics meets Audit Practice.

An interactive Streamlit application that brings mathematical rigour to IT audit sampling decisions. Built on probability theory and statistical inference, not lookup tables.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red) ![CISA](https://img.shields.io/badge/CISA-Domain%202-teal) ![License](https://img.shields.io/badge/license-MIT-green)

---

## Why this exists

Most auditors size their samples using fixed lookup tables (e.g. "at 95% confidence and 5% TDR, test 60 items"). These tables work, but they hide the mathematics behind the decision — and they break down when your population is small, your expected deviation rate is non-zero, or you need to communicate sampling risk to a client.

This tool makes the underlying model explicit and interactive.

---

## Modules

### Module 1 — Attribute Sampling
Tests binary controls (pass/fail): user access reviews, change approvals, backup verifications.

**Mathematical foundation**
- Sample size: Normal approximation to the Binomial distribution (one-tailed)
- Finite Population Correction (FPC) for populations under ~500 items
- Post-testing evaluation: Clopper-Pearson exact confidence interval for the Upper Deviation Rate (UDR)
- Sampling risk quantification: Type I (over-reliance) and Type II (under-reliance) error probabilities

**Key formula**
```
n = Z² × p̂(1 − p̂) / e²

where:
  Z   = one-tailed z-score at desired confidence level
  p̂   = expected deviation rate (prior estimate)
  e   = precision gap = TDR − EDR (tolerable − expected)
```

**Visualisations**
- Sensitivity heatmap: required sample size across a grid of confidence levels × TDR values
- UDR curve: how the Upper Deviation Rate grows as deviations are found, with TDR threshold overlay

---

### Module 2 — Monetary Unit Sampling (MUS)
Tests monetary populations: accounts payable, payroll, procurement transactions.

**Mathematical foundation**
- Probability-Proportional-to-Size (PPS) sampling: each monetary unit is a sampling unit
- Poisson model for reliability factors: `R₀ = −ln(1 − CL)`
- Upper Error Limit (UEL) decomposed into three components:
  - Basic Precision: `SI × R₀`
  - Projected Misstatements: `Σ tᵢ × SI`
  - Incremental Allowance: `Σ tᵢ × (Rᵢ − Rᵢ₋₁ − 1) × SI`

**Why Poisson?**
The Poisson distribution models rare events in large populations — exactly the situation in MUS where misstatements are expected to be infrequent. The reliability factor R₀ at common confidence levels:

| Confidence | R₀     |
|-----------|--------|
| 85%       | 1.897  |
| 90%       | 2.303  |
| 95%       | 2.996  |
| 99%       | 4.605  |

**Visualisations**
- UEL waterfall: Basic Precision + Projected + Incremental vs Tolerable Misstatement
- Sample size curve: n as a function of confidence level

---

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/audit-sampling-tool.git
cd audit-sampling-tool

# Install dependencies
pip install streamlit scipy numpy plotly

# Run the app
python -m streamlit run app.py
```

**Requirements:** Python 3.11+

---

## Project structure

```
audit-sampling-tool/
├── app.py              # Streamlit UI — all modules
├── sampling_core.py    # Mathematical engine (pure Python, no UI)
└── README.md
```

`sampling_core.py` is intentionally decoupled from the UI. You can import it directly in your own scripts or Jupyter notebooks:

```python
from sampling_core import attribute_sample_size, mus_sample_size

# Size a sample for a user access review
result = attribute_sample_size(
    confidence_level=0.95,
    tolerable_deviation_rate=0.05,
    expected_deviation_rate=0.02,
    population_size=320,
)
print(result)
# {'n_infinite': 59, 'n_adjusted': 47, 'z_score': 1.6449, ...}

# Size a MUS sample for accounts payable
mus = mus_sample_size(
    population_value=5_000_000,
    tolerable_misstatement=150_000,
    confidence_level=0.95,
)
print(mus)
# {'sample_size': 100, 'sampling_interval': 50083.0, 'reliability_factor': 2.996, ...}
```

---

## Mathematical references

| Concept | Source |
|--------|--------|
| Attribute sampling — Normal approximation | AICPA Audit Sampling Guide (2014) |
| Clopper-Pearson exact interval | Clopper & Pearson (1934), *Biometrika* |
| MUS — Poisson reliability factors | AICPA Audit Sampling Guide; Leslie, Teitlebaum & Anderson (1979) |
| Finite Population Correction | Cochran, *Sampling Techniques* (3rd ed., 1977) |
| CISA alignment | ISACA CISA Review Manual — Domain 2 |

---

## CISA alignment

This project covers concepts from **CISA Domain 2: Information Systems Acquisition, Development and Testing**, specifically the audit planning and evidence-gathering standards relating to:

- Sampling risk (alpha and beta error)
- Statistical vs non-statistical sampling
- Evaluation of sample results and projection to the population

---

## Author

**Dimitrios** — IT Auditor at a Big 4 firm (Greece) | Applied Mathematics (BSc + MSc) | CISA candidate

Combining quantitative methods with IT audit to go beyond checkbox compliance.

[LinkedIn](https://linkedin.com/in/YOUR_PROFILE) · [GitHub](https://github.com/YOUR_USERNAME)

---

## License

MIT — use freely, attribution appreciated.
