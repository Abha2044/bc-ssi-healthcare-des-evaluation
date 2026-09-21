    # DES Evaluation of the BC-SSI Healthcare Architecture

This repository contains a discrete-event simulation (DES) for evaluating a
blockchain-enabled self-sovereign identity (BC-SSI) healthcare architecture.
It translates architecture decisions identified through ATAM analysis into
executable scenarios and measures latency, success, resilience, queueing,
resource use, and security-related behaviour.

The simulation compares three configurations:

- **Baseline:** the original architecture with the identified gaps open.
- **Capacity-matched:** baseline behaviour with the refined resource
  capacities. This separates provisioning effects from architectural effects.
- **Refined:** the proposed architecture with the identified refinements
  enabled.

The model is an analytical evaluation, not a production healthcare system.
Configuration values are modelling assumptions and must be justified from the
architecture description, literature, measurements, or sensitivity analysis.

## Simulation documentation

The completed simulation is documented in two review-oriented files:

- [`docs/simulation_design.md`](docs/simulation_design.md) explains the architecture variants, scenarios, arrival model, queued resources, execution parameters, experiments, measurements, and interpretation boundaries.
- [`docs/simulation_results.md`](docs/simulation_results.md) presents the main publication-scale results, selected figures, trade-offs, and limitations.

Concise result tables are available under [`docs/evidence/`](docs/evidence/), and the selected publication figures are available under [`docs/figures/`](docs/figures/).

These documents allow reviewers to understand the simulation design and findings without reconstructing them from the Python code and full request-level datasets.
## Healthcare scenarios

The main experiment evaluates ten scenarios:

1. Emergency access
2. Consent-based access
3. Consent revocation
4. Cross-organizational FHIR exchange
5. High-volume ingestion
6. Audit investigation
7. Trust-service failure
8. Laboratory-ingestion recovery
9. Multi-device access
10. Research donation

Each scenario is repeated with controlled random seeds. Requests pass through
scenario-specific architectural services represented by capacity-limited
resource pools.

## Additional experiments

The project includes:

- workload sensitivity at 1x, 2x, and 5x arrival rates;
- trust-service failure sensitivity;
- credential-status failure sensitivity;
- connector-capacity sensitivity;
- trust-cache TTL and stale-cache-risk analysis;
- session-revalidation and unauthorized-continuation analysis;
- shared mixed-workload evaluation across all scenarios;
- detailed resource utilization, waiting-time, and saturation reporting;
- capacity attribution using baseline, capacity-matched, and refined results;
- direct runtime tracking of ATAM gaps G1–G13; and
- grouped ablation analysis comparing individual refinement packages with the
  baseline and full refined architecture.

The ablation packages are grouped changes, not necessarily single parameters.
Some packages include associated resource capacities or failure parameters.
Therefore, their results show the performance of a refinement package and
should not be interpreted as a perfectly isolated causal effect.

## Project files

- `config_advanced.json`: development-scale configuration (1,200 seconds,
  10 replications, 120-second warm-up).
- `config_publication_scale.json`: publication-scale configuration
  (3,600 seconds, 30 replications, 300-second warm-up).
- `run_advanced_experiments.py`: simulation scenarios and experiments.
- `analyze_results.py`: confidence intervals, paired comparisons, latency
  percentiles, capacity attribution, and ablation statistics.
- `plot_advanced_results.py`: PNG and PDF publication figures.
- `verify_simulation.py`: configuration and result-integrity checks.
- `GAP_COVERAGE.md`: mapping between ATAM gaps, model behaviour, and scenarios.
- `requirements.txt`: Python dependencies.
-  `docs/simulation_design.md`: detailed simulation design and assumptions.
- `docs/simulation_results.md`: summarized publication results and interpretation.
- `docs/evidence/`: selected publication-scale result summaries.
- `docs/figures/`: selected publication figures.

Generated `results`, `figures`, `publication_results`, and
`publication_figures` directories are ignored by Git because they can be
reproduced from the committed code and configuration.

## Installation

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

On Windows Command Prompt, activate the environment with:

```bat
.venv\Scripts\activate
```

## Development-scale workflow

Run the simulation:

```bash
python run_advanced_experiments.py \
  --config config_advanced.json \
  --output-directory results
```

Run the statistical analysis:

```bash
python analyze_results.py --results-directory results
```

Verify the development configuration and results:

```bash
python verify_simulation.py
```

Generate figures:

```bash
python plot_advanced_results.py \
  --results-directory results \
  --figures-directory figures
```

## Publication-scale workflow

```bash
python run_advanced_experiments.py \
  --config config_publication_scale.json \
  --output-directory publication_results

python analyze_results.py \
  --results-directory publication_results

python plot_advanced_results.py \
  --results-directory publication_results \
  --figures-directory publication_figures
```

Publication-scale runs take longer because they use 30 replications and also
execute the sensitivity, mixed-workload, and ablation experiments.

## Main outputs

The simulation creates request-level and replication-level CSV files. Important
summaries include:

- `baseline_refined_by_replication.csv`
- `workload_sensitivity_summary.csv`
- `trust_failure_sensitivity_summary.csv`
- `credential_status_sensitivity_summary.csv`
- `connector_capacity_sensitivity_summary.csv`
- `cache_ttl_sensitivity_summary.csv`
- `session_revalidation_sensitivity_summary.csv`
- `mixed_workload_summary.csv`
- `mixed_workload_resource_summary.csv`
- `resource_saturation_summary.csv`
- `gap_tracking_summary.csv`
- `ablation_summary.csv`
- `statistical_confidence_intervals.csv`
- `statistical_paired_comparisons.csv`
- `capacity_attribution_summary.csv`
- `ablation_confidence_intervals.csv`
- `ablation_paired_comparisons.csv`
- `ablation_overall_confidence_intervals.csv`

Figures are saved in both PNG and PDF formats. They cover architecture and
scenario comparisons, workload, fault sensitivity, cache and revalidation
trade-offs, capacity attribution, resource saturation, mixed-workload
stability, ATAM-gap tracking, and ablation outcomes.

## Interpreting the results

- Lower latency is better, but very large latency can indicate an unstable or
  censored queue rather than a realistic response time.
- A lower request success rate caused by explicit credential-status rejection
  can represent stronger security rather than poorer reliability.
- Capacity-matched results estimate how much improvement comes from additional
  provisioning while retaining baseline behaviour.
- Ablation results show whether one refinement package is sufficient; they do
  not prove that individual effects are additive.
- Confidence intervals describe simulation uncertainty under the configured
  assumptions, not uncertainty in the assumptions themselves.

For ATAM-gap definitions and their scenario mappings, see `GAP_COVERAGE.md`.
