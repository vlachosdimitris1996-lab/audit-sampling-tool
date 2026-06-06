"""
audit_sampling_core.py
======================
Core mathematical functions for IT Audit statistical sampling.

Mathematical foundations:
  - Attribute Sampling   : Binomial model → Normal/Poisson approximation
  - Monetary Unit Sampling (MUS) : Poisson-based upper error limit
  - Hypergeometric model : Exact finite-population correction

Author  : Dimitrios (IT Auditor & Applied Mathematician)
CISA    : Domain 2 – Information Systems Acquisition, Development and Testing
          (Audit Planning & Evidence – sampling standards)
"""

import math
from scipy import stats
from scipy.stats import hypergeom, binom, poisson
import numpy as np


# ─────────────────────────────────────────────────────────────
# 1. ATTRIBUTE SAMPLING
#    "What sample size do I need to test a binary control
#     (pass/fail) with a given confidence level?"
# ─────────────────────────────────────────────────────────────

def attribute_sample_size(
    confidence_level: float,
    tolerable_deviation_rate: float,
    expected_deviation_rate: float,
    population_size: int | None = None,
) -> dict:
    """
    Calculate sample size for attribute sampling.

    Uses the Normal approximation to the Binomial for large populations,
    with Finite Population Correction (FPC) when population_size is given.

    Parameters
    ----------
    confidence_level        : e.g. 0.95 for 95%
    tolerable_deviation_rate: Maximum deviation rate auditor will accept (e.g. 0.05)
    expected_deviation_rate : Auditor's prior estimate of actual deviation rate (e.g. 0.02)
    population_size         : If provided, applies Finite Population Correction

    Returns
    -------
    dict with:
        n_infinite  : Sample size for infinite population
        n_adjusted  : Sample size after FPC (if population_size given)
        z_alpha     : Z-score used
        margin      : tolerable_deviation_rate - expected_deviation_rate (precision gap)

    Mathematical basis
    ------------------
    Infinite population:
        n = (Z_{α/2})² * p̂(1 - p̂) / e²
    where:
        p̂ = expected_deviation_rate
        e  = tolerable_deviation_rate - expected_deviation_rate  (allowable margin)
        Z  = one-tailed z-score (audit sampling uses one-tail: risk of over-reliance)

    Finite Population Correction:
        n_adj = n / (1 + (n - 1) / N)
    """
    if expected_deviation_rate >= tolerable_deviation_rate:
        raise ValueError(
            "Expected deviation rate must be less than tolerable deviation rate. "
            "If expected ≥ tolerable, the control should not be relied upon."
        )

    # One-tailed z (auditor cares about upper tail — too many deviations)
    z = stats.norm.ppf(confidence_level)

    p = expected_deviation_rate
    e = tolerable_deviation_rate - expected_deviation_rate  # precision gap

    # Infinite population sample size
    n_inf = math.ceil((z**2 * p * (1 - p)) / (e**2))

    result = {
        "n_infinite": n_inf,
        "n_adjusted": None,
        "z_score": round(z, 4),
        "precision_gap": round(e, 4),
        "confidence_level": confidence_level,
        "tolerable_deviation_rate": tolerable_deviation_rate,
        "expected_deviation_rate": expected_deviation_rate,
        "method": "Normal approximation to Binomial (one-tailed)",
    }

    if population_size:
        n_adj = math.ceil(n_inf / (1 + (n_inf - 1) / population_size))
        result["n_adjusted"] = n_adj
        result["population_size"] = population_size
        result["fpc_factor"] = round(n_adj / n_inf, 4)

    return result


def attribute_upper_deviation_rate(
    sample_size: int,
    deviations_found: int,
    confidence_level: float,
) -> dict:
    """
    Calculate the Upper Deviation Rate (UDR) after testing.

    This answers: "I tested n items, found k deviations.
    What is the maximum true deviation rate in the population
    at my confidence level?"

    Uses the exact Binomial (Clopper-Pearson) confidence interval.

    Parameters
    ----------
    sample_size       : n — number of items tested
    deviations_found  : k — number of deviations found
    confidence_level  : e.g. 0.95

    Returns
    -------
    dict with upper_deviation_rate, point_estimate, and interpretation
    """
    alpha = 1 - confidence_level

    # Clopper-Pearson exact upper bound
    if deviations_found == 0:
        # Special case: no deviations found
        upper = 1 - alpha ** (1 / sample_size)
    else:
        upper = stats.beta.ppf(1 - alpha, deviations_found + 1, sample_size - deviations_found)

    point_estimate = deviations_found / sample_size

    return {
        "upper_deviation_rate": round(upper, 4),
        "point_estimate": round(point_estimate, 4),
        "sample_size": sample_size,
        "deviations_found": deviations_found,
        "confidence_level": confidence_level,
        "method": "Clopper-Pearson exact Binomial interval",
        "interpretation": (
            f"At {confidence_level*100:.0f}% confidence, the true deviation rate "
            f"in the population does not exceed {upper*100:.2f}%."
        ),
    }


# ─────────────────────────────────────────────────────────────
# 2. MONETARY UNIT SAMPLING (MUS)
#    "I want to test the monetary value of transactions.
#     How do I size my sample and evaluate misstatements?"
# ─────────────────────────────────────────────────────────────

def mus_sample_size(
    population_value: float,
    tolerable_misstatement: float,
    confidence_level: float,
    expected_misstatement: float = 0.0,
) -> dict:
    """
    Calculate MUS sample size using the Poisson model.

    MUS (also called Dollar Unit Sampling or Probability-Proportional-to-Size)
    treats each monetary unit as a sampling unit. Large-value items have a
    proportionally higher chance of selection.

    Parameters
    ----------
    population_value      : Total book value of the population (e.g. €5,000,000)
    tolerable_misstatement: Maximum error auditor can accept (e.g. €150,000)
    confidence_level      : e.g. 0.95
    expected_misstatement : Auditor's estimate of likely misstatement (default 0)

    Returns
    -------
    dict with sample_size, sampling_interval, and key parameters

    Mathematical basis
    ------------------
    Under the Poisson model (industry standard: AICPA / ISACA approach):

        Reliability factor R = -ln(1 - confidence_level)   [zero misstatements case]

        Sampling interval  I = Tolerable Misstatement / R

        Sample size        n = Population Value / I

    When expected misstatements > 0, an expansion factor is applied:
        I_adj = Tolerable Misstatement / (R + expansion_factor)
    """
    # Poisson reliability factor (zero misstatements)
    r_factor = -math.log(1 - confidence_level)

    # Expansion factor for expected misstatements
    # Based on Poisson distribution percentile for expected errors
    if expected_misstatement > 0:
        expected_errors = expected_misstatement / (population_value / (population_value / tolerable_misstatement))
        # Conservative expansion: add Poisson reliability for expected errors
        expansion = poisson.ppf(confidence_level, expected_errors) - expected_errors
        effective_r = r_factor + expansion
    else:
        effective_r = r_factor
        expansion = 0.0

    sampling_interval = tolerable_misstatement / effective_r
    sample_size = math.ceil(population_value / sampling_interval)

    return {
        "sample_size": sample_size,
        "sampling_interval": round(sampling_interval, 2),
        "reliability_factor": round(r_factor, 4),
        "expansion_factor": round(expansion, 4),
        "effective_reliability_factor": round(effective_r, 4),
        "population_value": population_value,
        "tolerable_misstatement": tolerable_misstatement,
        "confidence_level": confidence_level,
        "expected_misstatement": expected_misstatement,
        "method": "Poisson (Probability-Proportional-to-Size)",
    }


def mus_upper_error_limit(
    population_value: float,
    sample_size: int,
    confidence_level: float,
    misstatements: list[dict] | None = None,
) -> dict:
    """
    Calculate the Upper Error Limit (UEL) after MUS testing.

    Parameters
    ----------
    population_value  : Total book value
    sample_size       : n — items tested
    confidence_level  : e.g. 0.95
    misstatements     : List of dicts: [{"book_value": x, "audit_value": y}, ...]
                        If None or empty, assumes no misstatements found.

    Returns
    -------
    dict with uel, basic_precision, and misstatement details

    Mathematical basis
    ------------------
    UEL = Basic Precision + Projected Misstatements + Incremental Allowance

    Basic Precision  = (Population Value / n) * R_0
    where R_0 = Poisson reliability factor for 0 misstatements

    For each ranked misstatement (tainting factor t_i):
        Projected Misstatement_i  = t_i * Sampling Interval
        Incremental Allowance_i   = t_i * (R_i - R_{i-1} - 1) * Sampling Interval
    """
    if misstatements is None:
        misstatements = []

    sampling_interval = population_value / sample_size
    alpha = 1 - confidence_level

    # Poisson reliability factors for 0, 1, 2, ... misstatements
    # These are standard audit tables derived from Poisson CDF
    def poisson_reliability_factor(k: int) -> float:
        """R_k = Poisson upper bound for k misstatements at confidence level."""
        return -math.log(alpha) + sum(
            math.log(-math.log(alpha)) - math.log(j)
            for j in range(1, k + 1)
        ) if k > 0 else -math.log(alpha)

    r0 = poisson_reliability_factor(0)
    basic_precision = sampling_interval * r0

    if not misstatements:
        return {
            "upper_error_limit": round(basic_precision, 2),
            "basic_precision": round(basic_precision, 2),
            "projected_misstatements": 0.0,
            "incremental_allowance": 0.0,
            "misstatement_count": 0,
            "sampling_interval": round(sampling_interval, 2),
            "reliability_factor_r0": round(r0, 4),
            "interpretation": (
                f"No misstatements found. UEL = Basic Precision = €{basic_precision:,.2f}"
            ),
        }

    # Calculate tainting factors and sort descending (largest first)
    tainted = []
    for m in misstatements:
        bv = m["book_value"]
        av = m["audit_value"]
        taint = (bv - av) / bv if bv > 0 else 0.0
        tainted.append(taint)
    tainted.sort(reverse=True)

    projected_total = 0.0
    incremental_total = 0.0

    for i, t in enumerate(tainted):
        r_prev = poisson_reliability_factor(i)
        r_curr = poisson_reliability_factor(i + 1)
        projected_total += t * sampling_interval
        incremental_total += t * (r_curr - r_prev - 1) * sampling_interval

    uel = basic_precision + projected_total + incremental_total

    return {
        "upper_error_limit": round(uel, 2),
        "basic_precision": round(basic_precision, 2),
        "projected_misstatements": round(projected_total, 2),
        "incremental_allowance": round(incremental_total, 2),
        "misstatement_count": len(misstatements),
        "tainting_factors": [round(t, 4) for t in tainted],
        "sampling_interval": round(sampling_interval, 2),
        "interpretation": (
            f"Upper Error Limit = €{uel:,.2f}. "
            f"{'ACCEPTABLE' if uel <= 0 else 'Compare to Tolerable Misstatement to conclude.'}"
        ),
    }


# ─────────────────────────────────────────────────────────────
# 3. HYPERGEOMETRIC MODEL
#    Exact calculation for small / finite populations
#    (e.g. testing all system administrators in a company of 50)
# ─────────────────────────────────────────────────────────────

def hypergeometric_sample_size(
    population_size: int,
    tolerable_deviation_rate: float,
    confidence_level: float,
    expected_deviations: int = 0,
) -> dict:
    """
    Exact sample size using the Hypergeometric distribution.

    Preferred when population is small (N < 200) or sampling fraction > 10%.
    The Normal approximation overestimates sample size in these cases.

    Parameters
    ----------
    population_size          : N — total population items
    tolerable_deviation_rate : Maximum acceptable proportion of deviates
    confidence_level         : e.g. 0.95
    expected_deviations      : k — expected number of deviations in population

    Returns
    -------
    dict with optimal sample size and model details

    Mathematical basis
    ------------------
    Find minimum n such that:
        P(X ≤ expected_deviations | N, K, n) ≥ confidence_level

    where K = floor(N * tolerable_deviation_rate) is the maximum tolerable
    number of deviations in the population, and X ~ Hypergeometric(N, K, n).
    """
    K = math.floor(population_size * tolerable_deviation_rate)

    if K == 0:
        return {
            "error": "Tolerable deviation rate too low — implies 0 tolerable deviations in population.",
            "population_size": population_size,
            "K_tolerable_deviations": K,
        }

    # Search for minimum n
    for n in range(1, population_size + 1):
        # P(X <= expected_deviations) using Hypergeometric CDF
        prob = hypergeom.cdf(expected_deviations, population_size, K, n)
        if prob >= confidence_level:
            # n gives us the desired confidence — but we want 1 - confidence_level
            # Actually: we want prob of finding at least 1 deviation to be >= CL
            # P(X >= 1) = 1 - P(X = 0) >= confidence_level
            pass

        p_zero = hypergeom.pmf(0, population_size, K, n)
        if (1 - p_zero) >= confidence_level:
            return {
                "sample_size": n,
                "population_size": population_size,
                "K_max_tolerable_deviations": K,
                "tolerable_deviation_rate": tolerable_deviation_rate,
                "confidence_level": confidence_level,
                "p_detect_at_least_one": round(1 - p_zero, 6),
                "sampling_fraction": round(n / population_size, 4),
                "method": "Exact Hypergeometric",
                "note": (
                    "Use this model when N < 200 or sampling fraction > 10%. "
                    "The Normal approximation is conservative (gives larger n) for small populations."
                ),
            }

    return {"error": "Could not find valid sample size within population bounds."}


# ─────────────────────────────────────────────────────────────
# 4. SAMPLING RISK ANALYSIS
#    Quantify Alpha Risk (over-reliance) and Beta Risk (under-reliance)
# ─────────────────────────────────────────────────────────────

def sampling_risk_analysis(
    sample_size: int,
    deviations_found: int,
    tolerable_deviation_rate: float,
    population_size: int | None = None,
) -> dict:
    """
    Quantify Type I and Type II sampling risks.

    Type I  (Alpha) = Risk of over-reliance: concluding the control is effective
                      when it is NOT (false negative for auditor)
    Type II (Beta)  = Risk of under-reliance: concluding the control is NOT effective
                      when it IS (false positive for auditor — less critical)

    Parameters
    ----------
    sample_size              : n
    deviations_found         : k
    tolerable_deviation_rate : TDR — threshold defining "control failure"
    population_size          : N (optional, for exact Hypergeometric)

    Returns
    -------
    dict with alpha_risk, beta_risk, and decision recommendation
    """
    # Point estimate of population deviation rate
    point_estimate = deviations_found / sample_size

    # Alpha risk: P(conclude effective | true rate = TDR)
    # = P(X <= k | n, p = TDR) using Binomial
    alpha_risk = binom.cdf(deviations_found, sample_size, tolerable_deviation_rate)

    # Beta risk: P(conclude ineffective | true rate = 0)
    # = P(X >= k | n, p ≈ 0) — effectively P(X >= k | n, p = point_estimate/2)
    beta_rate = point_estimate / 2 if point_estimate > 0 else 0.001
    beta_risk = 1 - binom.cdf(deviations_found - 1, sample_size, beta_rate)

    # Decision
    if point_estimate <= tolerable_deviation_rate * 0.5:
        decision = "RELY — Point estimate well below TDR. Low sampling risk."
    elif point_estimate <= tolerable_deviation_rate:
        decision = "RELY WITH CAUTION — Point estimate below TDR but close. Consider expanding sample."
    else:
        decision = "DO NOT RELY — Point estimate exceeds TDR. Control cannot be relied upon."

    return {
        "point_estimate": round(point_estimate, 4),
        "tolerable_deviation_rate": tolerable_deviation_rate,
        "alpha_risk": round(alpha_risk, 4),
        "beta_risk": round(beta_risk, 4),
        "sample_size": sample_size,
        "deviations_found": deviations_found,
        "decision": decision,
        "interpretation": {
            "alpha": f"There is a {alpha_risk*100:.1f}% chance of over-relying on a failed control.",
            "beta": f"There is a {beta_risk*100:.1f}% chance of under-relying on an effective control.",
        },
    }


# ─────────────────────────────────────────────────────────────
# 5. HELPER: SENSITIVITY ANALYSIS
#    "How does my sample size change if I tweak parameters?"
# ─────────────────────────────────────────────────────────────

def sensitivity_analysis(
    base_confidence: float,
    base_tdr: float,
    base_edr: float,
    population_size: int | None = None,
) -> list[dict]:
    """
    Generate a grid of sample sizes across confidence levels and TDR values.
    Useful for visualizing the sensitivity of n to parameter choices.

    Returns a list of dicts suitable for a pandas DataFrame or Plotly heatmap.
    """
    confidence_levels = [0.85, 0.90, 0.95, 0.99]
    tdr_values = [
        max(base_edr + 0.01, base_tdr - 0.03),
        base_tdr,
        base_tdr + 0.03,
        base_tdr + 0.05,
    ]

    results = []
    for cl in confidence_levels:
        for tdr in tdr_values:
            if tdr <= base_edr:
                continue
            try:
                r = attribute_sample_size(cl, tdr, base_edr, population_size)
                n = r["n_adjusted"] if r["n_adjusted"] else r["n_infinite"]
                results.append({
                    "confidence_level": cl,
                    "tolerable_deviation_rate": round(tdr, 3),
                    "expected_deviation_rate": base_edr,
                    "sample_size": n,
                })
            except ValueError:
                pass

    return results
