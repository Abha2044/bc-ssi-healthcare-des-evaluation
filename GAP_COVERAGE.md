# Gap coverage: Appendix A to simulation mapping

Appendix A records thirteen gaps across the fifteen ATAM scenarios. This table states
exactly how each is represented in the discrete-event model, so that no claim is made
in the paper that the code does not support.

| Gap | Description | Modelled | How | Config flag |
|---|---|---|---|---|
| G1 | C15 only partially operationalised in Integration | Yes | `fhir_processing()` adds a cross-layer round-trip penalty when the capability is incomplete | `fhir_complete_in_integration` |
| G2 | No obligation handling | Yes | `policy_and_obligation_handling()` omits obligation execution when the capability is unavailable | `obligation_handling_enabled` |
| G3 | Data minimisation specified but not operationalised | Yes | `data_minimisation()` is a no-op in the baseline | `data_minimization_enabled` |
| G4 | Trust verification unavailable where consent is evaluated | Partial | Flag is carried in config and reported, but the model does not separate per-layer trust instances | `trust_in_privacy_layer` |
| G5 | Compliance recording optional and Privacy-layer only | Yes | `compliance_recording()` skips entirely outside Privacy; inside Privacy it is deployed with a configurable probability | `compliance_required` |
| G6 | No structured audit tagging | Yes | Recorded on every logged event; drives `audit_reconstruction()` failure | `audit_tagging_enabled` |
| G7 | Connector deployed as a single instance | Yes | No failover on connector failure; capacity 1 | `connector_redundancy_enabled` |
| G8 | Connector subcomponents incomplete in Access | Yes | Access-layer invocations take a degraded path with added delay | `connector_full_in_access` |
| G9 | No trust cache or fallback | Yes | Full on-chain lookup every time; no fallback on failure | `trust_cache_enabled`, `fallback_trust_enabled` |
| G10 | No session management | Yes | Unauthorised window drawn from an exponential with mean inter-request time, **not** bounded by a revalidation interval | `session_manager_enabled` |
| G11 | No anonymisation capability | Yes | `anonymization_processing()` is a no-op when the capability is unavailable | `anonymization_enabled` |
| G12 | No cross-device session/consent synchronisation | Yes | Consent change on device 2 does not reach device 1; sets `consent_divergence` | `cross_device_sync_enabled` |
| G13 | No degraded-mode operation or retry policy | Yes | Baseline has one attempt and no breaker, so it absorbs the full timeout | `circuit_breaker_enabled`, `max_retry_attempts` |

**G4 is the one partial case.** The model treats trust resolution as a single shared
service rather than as per-layer instances, so it cannot show a consent flow failing
because trust is unreachable in the Privacy layer specifically. The flag is present and
reported for completeness, but any claim about G4 should rest on the Appendix B trace
evidence (S2 step 5, S12 step 5) rather than on simulation output.

## Runtime tracking outputs

Every simulated request records the open gaps relevant to the scenario and
architecture in the `gaps_encountered` column of
`baseline_refined_detail.csv`. Gap identifiers are stored in numeric order,
for example `G2|G3|G5|G6|G9`.

The simulation also creates:

- `gap_tracking_by_replication.csv`, containing the affected request count and
  encounter rate for every architecture, scenario, replication and gap; and
- `gap_tracking_summary.csv`, containing averages across replications.

The capacity-matched architecture intentionally reports the same gaps as the
baseline because it changes only resource capacities. The refined architecture
reports no open gaps when every corresponding capability is enabled. G4 is
included in the summaries with `runtime_model_status=partial` and an encounter
rate of zero; it must not be presented as simulation-validated.

## Scenario mapping

| Simulation scenario | Appendix B scenario | Gaps exercised |
|---|---|---|
| `emergency_access` | S1 | G2, G3, G5, G6, G9 |
| `consent_based_access` | S2 | G2, G3, G5, G6, G9, G10, G13 |
| `lab_ingestion_recovery` | S3 | G1, G5, G6, G7, G9, G13 |
| `cross_org_exchange` | S4 | G2, G3, G5, G6, G7, G8, G9, G13 |
| `research_donation` | S5 | G1, G2, G5, G6, G9, G11 |
| `high_volume_ingestion` | S7 | G1, G5, G6, G7, G9, G13 |
| `multi_device_access` | S9 | G6, G9, G10, G12, G13 |
| `audit_investigation` | S10 | G2, G3, G5, G6, G9 |
| `consent_revocation` | S12 | G2, G5, G6, G9, G10, G13 |
| `trust_failure` | S14 | G5, G6, G9, G13 |

Five ATAM scenarios have no simulation counterpart: S6 escalation, S8 role change,
S11 registration, S13 pharmacy, S15 IoT streaming. Each is a variant of a modelled
flow and none exercises a gap that is not already covered, so their absence does not
reduce gap coverage. It does mean the simulation covers ten of fifteen scenarios, and
the paper should say so rather than implying full coverage.

## Parameter alignment with Appendix A

Service-time, failure-probability and capability assumptions are stored in
`config_advanced.json`. Publication-scale execution settings are stored in
`config_publication_scale.json`. Any numerical claim in the paper should be
generated from the committed configuration and result-analysis workflow rather
than copied from an earlier pilot run.