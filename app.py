"""
Audit Sampling Tool — Streamlit App
Module 1: Attribute Sampling
Module 2: Monetary Unit Sampling (MUS)

Run with:
    pip install streamlit scipy numpy plotly
    streamlit run app.py
"""

import math
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from sampling_core import (
    attribute_sample_size,
    attribute_upper_deviation_rate,
    sampling_risk_analysis,
    sensitivity_analysis,
    mus_sample_size,
    mus_upper_error_limit,
)

st.set_page_config(page_title="Audit Sampling Tool", page_icon="📐", layout="wide")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0f1117; }
    .metric-card { background: #1a1d27; border: 1px solid #2d3147; border-radius: 10px; padding: 1.2rem 1.5rem; margin-bottom: 0.5rem; }
    .metric-label { font-size: 0.75rem; color: #8b8fa8; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 4px; }
    .metric-value { font-size: 2rem; font-weight: 600; color: #e8eaf0; }
    .metric-sub   { font-size: 0.72rem; color: #5c6078; margin-top: 4px; }
    .formula-box  { background: #13161f; border: 1px solid #2d3147; border-radius: 8px; padding: 1rem 1.25rem; font-family: monospace; font-size: 0.85rem; color: #a0a8c8; margin: 0.5rem 0; line-height: 1.8; }
    .rely-green   { background: #0d2218; border-left: 3px solid #1D9E75; border-radius: 8px; padding: 1rem; }
    .rely-amber   { background: #1f1a0c; border-left: 3px solid #EF9F27; border-radius: 8px; padding: 1rem; }
    .no-rely-red  { background: #1f0d0d; border-left: 3px solid #E24B4A; border-radius: 8px; padding: 1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 📐 Audit Sampling Tool")
st.markdown("<p style='color:#8b8fa8; margin-top:-0.5rem;'>Statistical sampling for IT audit — Applied Mathematics meets Audit Practice</p>", unsafe_allow_html=True)
st.divider()

tab1, tab2 = st.tabs(["Module 1 — Attribute Sampling", "Module 2 — Monetary Unit Sampling (MUS)"])


# ════════════════════════════════════════════════════════════
# MODULE 1
# ════════════════════════════════════════════════════════════
with tab1:
    with st.sidebar:
        st.markdown("### Module 1 — Parameters")
        confidence_level = st.slider("Confidence level", 0.80, 0.99, 0.95, 0.01, format="%.2f")
        tdr = st.slider("Tolerable Deviation Rate (TDR)", 0.01, 0.20, 0.05, 0.01, format="%.2f")
        edr = st.slider("Expected Deviation Rate (EDR)", 0.00, 0.10, 0.02, 0.01, format="%.2f")
        use_fpc = st.toggle("Apply Finite Population Correction (FPC)", value=False)
        population_size = None
        if use_fpc:
            population_size = st.number_input("Population size (N)", 10, 10000, 500, 10)
        st.divider()
        st.markdown("### Evaluate results")
        n_tested = st.number_input("Sample size tested (n)", 1, 2000, 60)
        k_found  = st.number_input("Deviations found (k)",   0, 500,   1)

    if edr >= tdr:
        st.error("⚠️ Expected Deviation Rate must be < Tolerable Deviation Rate.")
        st.stop()

    sample_result = attribute_sample_size(confidence_level, tdr, edr, population_size)
    udr_result    = attribute_upper_deviation_rate(n_tested, k_found, confidence_level)
    risk_result   = sampling_risk_analysis(n_tested, k_found, tdr)

    n_display = sample_result["n_adjusted"] if sample_result["n_adjusted"] else sample_result["n_infinite"]
    n_label   = f"FPC applied — infinite: {sample_result['n_infinite']}" if sample_result["n_adjusted"] else "Infinite population (no FPC)"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Required sample size</div><div class="metric-value">{n_display}</div><div class="metric-sub">{n_label}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Z-score (one-tailed)</div><div class="metric-value">{sample_result["z_score"]:.3f}</div><div class="metric-sub">Normal approx. to Binomial</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Precision gap (TDR − EDR)</div><div class="metric-value">{sample_result["precision_gap"]*100:.1f}%</div><div class="metric-sub">Allowable margin of error</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Upper Deviation Rate</div><div class="metric-value">{udr_result["upper_deviation_rate"]*100:.2f}%</div><div class="metric-sub">Clopper-Pearson exact · k={k_found}, n={n_tested}</div></div>', unsafe_allow_html=True)

    col_f, col_d = st.columns(2)
    with col_f:
        st.markdown("##### Formula applied")
        z, p, e = sample_result["z_score"], edr, sample_result["precision_gap"]
        st.markdown(f'<div class="formula-box">n = Z² × p̂(1−p̂) / e²<br>n = {z:.3f}² × {p:.2f} × {1-p:.2f} / {e:.3f}²<br><strong style="color:#e8eaf0">n = {n_display}</strong></div>', unsafe_allow_html=True)
    with col_d:
        st.markdown("##### Sampling decision")
        dec = risk_result["decision"]
        alpha_r, beta_r, pt = risk_result["alpha_risk"], risk_result["beta_risk"], risk_result["point_estimate"]
        css = "no-rely-red" if "DO NOT" in dec else ("rely-amber" if "CAUTION" in dec else "rely-green")
        icon = "🔴" if "DO NOT" in dec else ("🟡" if "CAUTION" in dec else "🟢")
        st.markdown(f'<div class="{css}"><strong>{icon} {dec}</strong><br><br><span style="font-size:0.8rem;color:#8b8fa8;">Point estimate: {pt*100:.1f}% · UDR: {udr_result["upper_deviation_rate"]*100:.2f}% · TDR: {tdr*100:.1f}%<br>α-risk: {alpha_r*100:.1f}% · β-risk: {beta_r*100:.1f}%</span></div>', unsafe_allow_html=True)

    st.divider()
    col_heat, col_line = st.columns([1.2, 1])

    with col_heat:
        st.markdown("##### Sensitivity — n by confidence × TDR")
        sens = sensitivity_analysis(confidence_level, tdr, edr, population_size)
        if sens:
            cl_vals  = sorted(set(r["confidence_level"] for r in sens))
            tdr_vals = sorted(set(r["tolerable_deviation_rate"] for r in sens))
            z_matrix = [[next((r["sample_size"] for r in sens if r["confidence_level"]==cl and r["tolerable_deviation_rate"]==t), None) for t in tdr_vals] for cl in cl_vals]
            fig = go.Figure(go.Heatmap(z=z_matrix, x=[f"{t*100:.0f}%" for t in tdr_vals], y=[f"{c*100:.0f}%" for c in cl_vals],
                colorscale="Teal", text=[[str(v) if v else "—" for v in row] for row in z_matrix], texttemplate="%{text}", showscale=True))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b8fa8"),
                margin=dict(l=20,r=20,t=10,b=40), xaxis_title="TDR", yaxis_title="Confidence level", height=280)
            st.plotly_chart(fig, use_container_width=True)

    with col_line:
        st.markdown("##### UDR vs deviations found (k)")
        k_range  = list(range(0, min(n_tested+1, 20)))
        udr_vals = [attribute_upper_deviation_rate(n_tested, k, confidence_level)["upper_deviation_rate"]*100 for k in k_range]
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=k_range, y=udr_vals, mode="lines+markers", line=dict(color="#1D9E75", width=2), marker=dict(size=6)))
        fig2.add_hline(y=tdr*100, line_dash="dash", line_color="#E24B4A", annotation_text=f"TDR={tdr*100:.0f}%", annotation_font_color="#E24B4A")
        fig2.add_vline(x=k_found, line_dash="dot", line_color="#EF9F27", annotation_text=f"k={k_found}", annotation_font_color="#EF9F27")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b8fa8"),
            margin=dict(l=20,r=20,t=10,b=40), xaxis_title="Deviations found (k)", yaxis_title="UDR (%)", showlegend=False, height=280)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<p style='color:#3c4060;font-size:0.72rem;'>Normal approx. to Binomial · Clopper-Pearson exact · FPC · CISA Domain 2</p>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# MODULE 2: MUS
# ════════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### Monetary Unit Sampling (MUS) — Poisson model")
    st.markdown("<p style='color:#8b8fa8; font-size:0.85rem;'>Each monetary unit is a sampling unit. Items selected probability-proportional-to-size (PPS) — larger transactions have proportionally higher selection probability.</p>", unsafe_allow_html=True)

    col_in, col_out = st.columns([1, 1.2])

    with col_in:
        st.markdown("##### Population parameters")
        pop_value = st.number_input("Population value (€)", 100_000, 100_000_000, 5_000_000, 100_000, format="%d")
        tol_miss  = st.number_input("Tolerable misstatement (€)", 10_000, 5_000_000, 150_000, 10_000, format="%d")
        cl_mus    = st.slider("Confidence level", 0.80, 0.99, 0.95, 0.01, format="%.2f", key="cl_mus")
        exp_miss  = st.number_input("Expected misstatement (€)", 0, 1_000_000, 0, 10_000, format="%d")

        st.markdown("##### Misstatements found")
        st.caption("Enter book value and audit value for each misstatement discovered.")
        n_miss = st.number_input("Number of misstatements", 0, 10, 0)
        misstatements = []
        for i in range(n_miss):
            c1, c2 = st.columns(2)
            with c1: bv = st.number_input(f"Book value #{i+1} (€)", 0, 10_000_000, 10_000, key=f"bv{i}")
            with c2: av = st.number_input(f"Audit value #{i+1} (€)", 0, 10_000_000, 8_000, key=f"av{i}")
            if bv > 0:
                st.caption(f"Tainting factor: {(bv-av)/bv*100:.1f}%")
                misstatements.append({"book_value": bv, "audit_value": av})

    with col_out:
        mus_r = mus_sample_size(pop_value, tol_miss, cl_mus, exp_miss)
        uel_r = mus_upper_error_limit(pop_value, mus_r["sample_size"], cl_mus, misstatements if misstatements else None)

        st.markdown("##### Results")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Required sample size</div><div class="metric-value">{mus_r["sample_size"]:,}</div><div class="metric-sub">Poisson PPS model</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-card"><div class="metric-label">Reliability factor R₀</div><div class="metric-value">{mus_r["reliability_factor"]:.4f}</div><div class="metric-sub">−ln(1 − {cl_mus:.0%})</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Sampling interval</div><div class="metric-value">€{mus_r["sampling_interval"]:,.0f}</div><div class="metric-sub">TM / R₀</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-card"><div class="metric-label">TM as % of population</div><div class="metric-value">{tol_miss/pop_value*100:.2f}%</div><div class="metric-sub">Materiality threshold</div></div>', unsafe_allow_html=True)

        bp  = uel_r["basic_precision"]
        pm  = uel_r["projected_misstatements"]
        ia  = uel_r["incremental_allowance"]
        uel = uel_r["upper_error_limit"]

        st.markdown("##### Upper Error Limit (UEL)")
        st.markdown(f'<div class="formula-box">Basic precision &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; €{bp:>12,.0f}<br>Projected misstatements &nbsp; €{pm:>12,.0f}<br>Incremental allowance &nbsp;&nbsp;&nbsp; €{ia:>12,.0f}<br>──────────────────────────────────────<br><strong style="color:#e8eaf0">Total UEL &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; €{uel:>12,.0f}</strong><br>Tolerable misstatement &nbsp;&nbsp;&nbsp; €{tol_miss:>12,.0f}</div>', unsafe_allow_html=True)

        if uel <= tol_miss:
            st.markdown(f'<div class="rely-green"><strong>🟢 ACCEPTABLE — UEL within tolerable misstatement</strong><br><span style="font-size:0.8rem;color:#8b8fa8;">UEL €{uel:,.0f} ≤ TM €{tol_miss:,.0f}. Population is not materially misstated.</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="no-rely-red"><strong>🔴 UNACCEPTABLE — UEL exceeds tolerable misstatement</strong><br><span style="font-size:0.8rem;color:#8b8fa8;">UEL €{uel:,.0f} > TM €{tol_miss:,.0f}. Extend testing or qualify the conclusion.</span></div>', unsafe_allow_html=True)

    st.divider()
    col_bar, col_cl = st.columns(2)

    with col_bar:
        st.markdown("##### UEL components vs tolerable misstatement")
        fig_bar = go.Figure(go.Bar(
            x=["Basic precision", "Projected misstatements", "Incremental allowance", "Tolerable misstatement"],
            y=[bp, pm, ia, tol_miss],
            marker_color=["#1D9E75", "#EF9F27", "#D85A30", "rgba(226,75,74,0.5)"],
            marker_line_color=["#0F6E56", "#BA7517", "#993C1D", "#A32D2D"], marker_line_width=1,
        ))
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b8fa8"), showlegend=False, margin=dict(l=20,r=20,t=10,b=60), height=300,
            yaxis=dict(tickprefix="€", tickformat=",.0f", gridcolor="rgba(136,135,128,0.1)"),
            xaxis=dict(tickangle=-10))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_cl:
        st.markdown("##### Sample size vs confidence level (fixed TM)")
        cl_range = np.arange(0.80, 0.995, 0.005)
        n_range  = [mus_sample_size(pop_value, tol_miss, float(c), exp_miss)["sample_size"] for c in cl_range]
        fig_cl = go.Figure()
        fig_cl.add_trace(go.Scatter(x=[round(c*100, 1) for c in cl_range], y=n_range,
            mode="lines", line=dict(color="#5DCAA5", width=2)))
        fig_cl.add_vline(x=round(cl_mus*100, 1), line_dash="dot", line_color="#EF9F27",
            annotation_text=f"Current: {cl_mus*100:.0f}%", annotation_font_color="#EF9F27")
        fig_cl.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b8fa8"), showlegend=False, margin=dict(l=20,r=20,t=10,b=40), height=300,
            xaxis=dict(title="Confidence level (%)", tickangle=-45, nticks=10, gridcolor="rgba(136,135,128,0.1)"),
            yaxis=dict(title="Sample size (n)", gridcolor="rgba(136,135,128,0.1)"))
        st.plotly_chart(fig_cl, use_container_width=True)

    st.markdown("<p style='color:#3c4060;font-size:0.72rem;'>Poisson reliability factors · PPS sampling · UEL = Basic Precision + Projected + Incremental · CISA Domain 2</p>", unsafe_allow_html=True)
