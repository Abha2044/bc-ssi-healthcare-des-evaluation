# Simulation design

## Purpose

The discrete-event simulation evaluates how the original and refined BC-SSI healthcare architectures behave under healthcare workflows, workload pressure, and service failures.

It provides model-level evidence about latency, reliability, queueing, resource utilization, resilience mechanisms, and selected security and governance capabilities.

The simulation does not represent a deployed hospital system. Its parameters are modelling assumptions used to compare architecture variants under controlled conditions.

## Questions addressed

The simulation examines four questions:

1. How do the baseline and refined architectures behave across the selected healthcare scenarios?
2. How much improvement comes from additional service capacity, and how much comes from changed architectural behaviour?
3. Which shared resources become bottlenecks as workload increases?
4. How do failure-handling and security mechanisms affect performance and request outcomes?

## Architecture variants

| Variant | Definition | Purpose |
|---|---|---|
| Baseline | Original architecture with identified capabilities absent or incomplete | Provides the reference configuration |
| Capacity-matched | Baseline behaviour using the refined resource capacities | Separates the effect of additional capacity |
| Refined | Proposed capabilities and refined capacities enabled | Evaluates the combined architectural refinement |

The capacity-matched variant is important because a direct comparison between baseline and refined configurations would mix two effects: additional processing capacity and different architectural behaviour.

## Publication-scale execution

The publication configuration is stored in `config_publication_scale.json`.

| Parameter | Value |
|---|---:|
| Simulation duration | 3,600 seconds |
| Warm-up period | 300 seconds |
| Measurement window | 3,300 seconds |
| Replications | 30 |
| Base random seed | 42 |
| Common random numbers | Enabled |
| Service-time distribution | Lognormal |

Requests arriving before the warm-up boundary are excluded from the measured request results.

Common random numbers provide comparable arrival and failure streams for the baseline, capacity-matched, and refined architectures within each scenario and replication.

## Arrival model

Each scenario uses a Poisson arrival process. The simulation generates exponentially distributed inter-arrival times until the simulation horizon.

| Scenario | Arrival rate per second |
|---|---:|
| Emergency access | 0.18 |
| Consent-based access | 0.20 |
| Consent revocation | 0.12 |
| Cross-organisational exchange | 0.15 |
| High-volume ingestion | 0.60 |
| Audit investigation | 0.005 |
| Trust failure | 0.10 |
| Laboratory-ingestion recovery | 0.10 |
| Multi-device access | 0.06 |
| Research donation | 0.05 |

## Queued service resources

The `ResourcePool` class represents a service with a configurable number of parallel service slots.

When all service slots are busy, a request waits for the next available slot. The simulation records busy time, utilization, average and maximum waiting time, saturation, and calls whose service begins after the simulation horizon.

The simulation contains these queued resources:

- trust service;
- credential-status service;
- credential verifier;
- policy engine;
- FHIR service;
- audit service;
- connector;
- asynchronous queue;
- orchestrator;
- session service;
- compliance recorder; and
- anonymizer.

Resource capacity is a simulation input. It is not a measurement of production hardware or observed real-world concurrency.

## Scenario flows

Each scenario represents a complete healthcare workflow that invokes a scenario-specific set of services and capabilities.

| Scenario | Main modeled path or concern |
|---|---|
| Emergency access | Credential and DID verification, trust resolution, status checking, policy and obligations, minimization, compliance, and audit |
| Consent-based access | Trust and status verification, consent and revocation handling, policy, minimization, FHIR processing, compliance, and audit |
| Consent revocation | Trust and status verification, policy, revocation propagation, compliance, and audit |
| Cross-organisational exchange | Trust, connector processing, status verification, policy, minimization, FHIR processing, compliance, and audit |
| High-volume ingestion | Connector, FHIR processing, trust sampling, compliance, and audit under a high arrival rate |
| Audit investigation | Audit reconstruction and the effect of structured audit tagging |
| Trust failure | Trust-service failure, retries, cached fallback, circuit breaking, and downstream processing |
| Laboratory-ingestion recovery | Connector and trust failures, queueing, retry and degraded behaviour, FHIR processing, compliance, and audit |
| Multi-device access | Trust, status, session and consent synchronization, policy, minimization, compliance, and audit |
| Research donation | Trust and status verification, policy, minimization, anonymization, compliance, audit, and FHIR processing |

The simulation measures complete request flows. Component delay and failure are interpreted in the context of interactions and dependencies within each flow.

## Refined mechanisms

The refined configuration enables or strengthens:

- FHIR processing across the required layer boundary;
- policy-obligation handling;
- data minimization;
- compliance recording;
- structured audit tagging;
- connector redundancy and complete access-layer connector behaviour;
- trust caching and time-bounded cached fallback;
- explicit credential-status checking;
- session management and cross-device synchronization;
- anonymization;
- retries, orchestration, and circuit breaking; and
- larger service capacities.

The simulation represents these mechanisms through changes in behaviour, delay, failure handling, retry, state, or resource capacity. Their presence in the simulation does not prove production correctness or legal compliance.

## Recorded outputs

Each request records:

- architecture, scenario, and replication;
- request start and end times;
- latency and success;
- failure reason;
- trust lookups and cache use;
- credential-status checking;
- retry, fallback, and circuit-breaker behaviour;
- obligation and minimization indicators;
- compliance and audit indicators;
- anonymization;
- revocation propagation; and
- unauthorized continuation.

Resource summaries record:

- configured service capacity;
- call count;
- utilization;
- average and maximum waiting time;
- saturation; and
- calls delayed beyond the simulation horizon.

## Experiments

The repository implements:

- main baseline, capacity-matched, and refined comparison;
- workload sensitivity at 1x, 2x, and 5x;
- trust-service failure sensitivity;
- credential-status failure sensitivity;
- connector-capacity sensitivity;
- trust-cache TTL and estimated stale-cache-risk analysis;
- session-revalidation sensitivity;
- shared mixed-workload evaluation;
- resource-saturation analysis;
- capacity attribution; and
- grouped refinement ablation.

## Statistical analysis and figures

`analyze_results.py` calculates:

- publication summaries;
- 95% Student-t confidence intervals across replications;
- paired architecture comparisons;
- P50, P95, P99, and maximum latency;
- capacity attribution; and
- ablation statistics.

`plot_advanced_results.py` generates publication figures in PNG and PDF formats.

`verify_simulation.py` checks configuration consistency, result completeness, valid numeric ranges, expected scenario and architecture coverage, and ablation outputs.

## Reproduction workflow

From the repository root:

```bash
python run_advanced_experiments.py \
  --config config_publication_scale.json \
  --output-directory publication_results

python analyze_results.py \
  --results-directory publication_results

python plot_advanced_results.py \
  --results-directory publication_results \
  --figures-directory publication_figures

python verify_simulation.py