# DES Evaluation of the BC-SSI Healthcare Architecture

This repository contains a discrete-event simulation (DES) for evaluating a
blockchain-enabled self-sovereign identity (BC-SSI) healthcare architecture.
The model translates architectural decisions identified through ATAM analysis
into executable healthcare scenarios and measures latency, success, resilience,
queueing, resource utilization, saturation, and security-related behaviour.

The simulation provides model-level evidence. It is not a deployed healthcare
system, a production benchmark, or proof of legal compliance, clinical safety,
FHIR conformance, or patient identity-matching correctness.

## Architecture configurations

The experiments compare three configurations:

- **Baseline:** the original architecture with the identified gaps open.
- **Capacity-matched:** baseline behaviour with resource capacities matched to
  the refined configuration. This separates additional provisioning from
  architectural change.
- **Refined:** the proposed architecture with the selected capabilities and
  resilience mechanisms enabled.

## Simulation documentation

- [`docs/simulation_design.md`](docs/simulation_design.md) describes the
  configurations, architecture variants, scenarios, arrival model, resources,
  experiments, measurements, assumptions, and evidence-generation process.
- [`docs/simulation_results.md`](docs/simulation_results.md) presents the main
  publication-scale results, figures, interpretations, and limitations.
- [`docs/evidence/`](docs/evidence/) contains curated numerical evidence that
  supports the documented results.
- [`docs/figures/`](docs/figures/) contains the selected publication figures
  referenced by the results documentation.

## Healthcare scenarios

The main DES experiment evaluates ten healthcare scenarios:

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

The DES covers ten of the fifteen ATAM scenarios. The remaining scenarios must
be assessed through architectural validation and must not be described as
runtime-validated by this simulation.

Each scenario is repeated using controlled random seeds. Requests follow
scenario-specific flows through capacity-limited resources representing
services such as trust resolution, policy evaluation, credential verification,
FHIR processing, auditing, compliance recording, session management, and
connector processing.

## Arrival-model assumptions

Scenario requests are generated using independent homogeneous Poisson arrival
processes with exponentially distributed inter-arrival times. The configured
rates are synthetic reference workloads.

Workload-sensitivity and mixed-workload experiments evaluate how conclusions
change when these reference rates are increased. They test comparative
robustness and modeled capacity limits; they do not establish that the reference
rates represent real operational demand.

## Experiments

The repository includes:

- the main baseline, capacity-matched, and refined comparison;
- workload-sensitivity analysis;
- trust-service failure sensitivity;
- credential-status failure sensitivity;
- connector-capacity sensitivity;
- trust-cache TTL and estimated stale-cache-risk analysis;
- session-revalidation and unauthorized-continuation analysis;
- shared mixed-workload evaluation across all ten scenarios;
- resource utilization, waiting-time, delayed-call, and saturation reporting;
- capacity attribution using the three architecture configurations;
- runtime tracking of modeled ATAM gaps; and
- grouped ablation analysis comparing individual refinement packages with the
  baseline and complete refined configuration.

The ablation variants are refinement packages rather than guaranteed
single-parameter interventions. Some packages include related capacity or
failure-parameter changes. Their results must therefore not be interpreted as
perfectly isolated causal effects.

## Project structure

### Configuration and execution

- `config_advanced.json`: development-scale configuration using a 1,200-second
  horizon, 120-second warm-up, and 10 replications.
- `config_publication_scale.json`: publication-scale configuration using a
  3,600-second horizon, 300-second warm-up, and 30 replications.
- `run_advanced_experiments.py`: implements scenarios, architecture variants,
  arrival processes, resources, failures, sensitivity experiments, mixed
  workloads, and ablation experiments.

### Analysis and verification

- `analyze_results.py`: calculates confidence intervals, paired comparisons,
  latency percentiles, capacity attribution, and ablation statistics.
- `plot_advanced_results.py`: generates PNG and PDF figures from analysed CSV
  results.
- `verify_simulation.py`: checks configuration consistency, expected outputs,
  completeness, valid ranges, and statistical-result integrity.

### Traceability and documentation

- `GAP_COVERAGE.md`: maps ATAM gaps to model behaviour and scenarios and states
  which concerns are partial or outside the DES scope.
- `docs/simulation_design.md`: detailed simulation methodology and evidence
  description.
- `docs/simulation_results.md`: summarized results and interpretation.
- `docs/evidence/`: curated publication-scale evidence tables.
- `docs/figures/`: selected publication figures.
- `requirements.txt`: Python dependencies.

Generated `results/`, `figures/`, `publication_results/`, and
`publication_figures/` directories are excluded from Git because they can be
recreated from the committed code and configuration. Selected evidence tables
and figures are committed under `docs/` so the principal results remain
directly accessible on GitHub.

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

Analyse the results:

```bash
python analyze_results.py --results-directory results
```

Generate figures:

```bash
python plot_advanced_results.py \
  --results-directory results \
  --figures-directory figures
```

Verify the configuration and generated results:

```bash
python verify_simulation.py
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

Publication-scale execution takes longer because it uses 30 replications and
also runs the sensitivity, mixed-workload, resource, and ablation experiments.

## Evidence-generation workflow

The evidence is produced in this order:

1. The configuration files define the duration, warm-up, replications, arrival
   rates, capacities, failure assumptions, and architecture capabilities.
2. `run_advanced_experiments.py` produces replication-level and summary CSV
   results.
3. `analyze_results.py` produces statistical and comparative evidence.
4. `plot_advanced_results.py` generates figures from the analysed CSV files.
5. `verify_simulation.py` checks that the configuration and generated evidence
   are complete and internally consistent.
6. The principal tables and figures are presented under `docs/`.

In compact form:

```text
Configuration
    -> simulation
    -> statistical analysis
    -> figures
    -> verification
    -> documentation
```

A detailed description of the generated CSV files belongs in
[`docs/simulation_design.md`](docs/simulation_design.md). The CSV files contain
the numerical evidence, while the figures provide visual summaries.

## Interpretation boundaries

- Lower latency is better, but extremely large latency may indicate unstable
  queue growth or unresolved backlog rather than an ordinary response time.
- A lower request-success rate caused by explicit credential-status rejection
  can represent safer fail-closed behaviour rather than weaker reliability.
- Capacity-matched results estimate how much modeled improvement is associated
  with additional provisioning while baseline behaviour is retained.
- Ablation results test refinement packages; they do not prove that individual
  effects are independent or additive.
- Confidence intervals quantify stochastic uncertainty across simulation
  replications under the configured assumptions. They do not quantify
  uncertainty in the assumptions themselves.
- Stress testing demonstrates comparative behaviour under increased modeled
  demand. It does not validate the workload as representative of a real
  healthcare deployment.

For detailed assumptions, evidence definitions, results, and limitations, see
the documentation under [`docs/`](docs/).
