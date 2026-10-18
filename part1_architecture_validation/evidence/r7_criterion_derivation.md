# R7 criterion derivation

Where each assessment criterion comes from, and what evidence it would take
to settle it. Generated from `r7_criterion_derivation.csv` in this folder -
edit the CSV, then re-run `make_derivation_md.py`.

Each criterion is derived from one element of the R7 requirement and one
documented interaction in the source appendices. The **evidence threshold**
column states, in advance, what would count as settling it. Thresholds were
fixed before the verdicts were recorded, so a verdict cannot be justified by
whatever evidence happened to be available.

**14 direct criteria** determine R7 coverage. **3 supplementary criteria are** reported separately.

## Summary

| Criterion | Scope | R7 element | Components | Baseline | C4\*+C6\* | Proposed |
| --- | --- | --- | --- | --- | --- | --- |
| `C4-DECISION` | Direct | Decide need-to-know access | C4 | supported | supported | supported |
| `C4-OBLIGATIONS` | Direct | Return mandatory restrictions with the decision | C4 | supported | supported | supported |
| `C6-DECISION` | Direct | Enforce permit or deny | C6 | supported | supported | supported |
| `C6-OBLIGATIONS-ASSIGNED` | Direct | Apply masking/filtering before disclosure | C6 | supported | supported | supported |
| `C6-OBLIGATIONS-MECHANISM` | Direct | A mechanism that applies the restrictions | C6 | **unresolved** | supported | supported |
| `C15-SCOPE` | Direct | Retrieve only authorized FHIR scope | C15 | supported | supported | supported |
| `I1-REQUEST` | Direct | Supply inputs for access decisions | C6 ↔ C4 | supported | supported | supported |
| `I2-RESPONSE` | Direct | Use a consistent decision/obligation contract | C4 ↔ C6 | **unresolved** | **unresolved** | supported |
| `I3-SCOPE` | Direct | Preserve authorized scope across retrieval | C6 ↔ C15 | **unresolved** | **unresolved** | supported |
| `I4-DATA` | Direct | Release only correctly restricted data | C6 ↔ C15 | **unresolved** | **unresolved** | supported |
| `STATE-POLICY` | Direct | Identify policy-definition owner | C4 / C4.2 | supported | supported | supported |
| `STATE-CONSENT` | Direct | Identify current consent-state owner | C4 / C4.2; C14 issues consent credentials | supported | supported | supported |
| `STATE-REQUEST` | Direct | Decide whether persistent request/session state is required | C6 | n/a | n/a | n/a |
| `STATE-CONSENT-COORDINATION` | Direct | Decide whether mid-request consent updates must be coordinated | C4 ↔ C14 | n/a | n/a | n/a |
| `C5-AUDIT` | Supplementary audit | Record allowed and denied access | C5 | supported | supported | supported |
| `I5-AUDIT` | Supplementary audit | Transmit audit event information | C6 ↔ C5 | **unresolved** | **unresolved** | **unresolved** |
| `C5-ENFORCEMENT-OUTCOME` | Supplementary audit | Record applied or blocked restrictions | C5 | **unresolved** | **unresolved** | **unresolved** |

## Criterion by criterion

### Direct criteria

#### `C4-DECISION` — Decide need-to-know access

- **Components:** C4
- **Source interaction:** C6 → C4: evaluate claims, purpose, consent; permit/deny (B §A R7; B Table C R7)
- **Why this is a criterion:** Access requires an authorization decision.
- **Evidence threshold:** Documented assignment of C4 as PDP issuing permit/deny; runtime correctness requires separate tests.
- **Baseline verdict:** supported
- **C4\*+C6\* verdict:** supported
- **Proposed design verdict:** supported

#### `C4-OBLIGATIONS` — Return mandatory restrictions with the decision

- **Components:** C4
- **Source interaction:** C4 → C6: decision + masking/date obligations (B §A R7; B Table C R7)
- **Why this is a criterion:** Permit alone does not capture need-to-know restrictions.
- **Evidence threshold:** Documented decision-plus-obligations responsibility; correct selection requires separate executable evidence.
- **Baseline verdict:** supported
- **C4\*+C6\* verdict:** supported
- **Proposed design verdict:** supported

#### `C6-DECISION` — Enforce permit or deny

- **Components:** C6
- **Source interaction:** C4 → C6: decision; C6 permits/denies (B §A R7; B Table C R7)
- **Why this is a criterion:** A PDP result must govern downstream access.
- **Evidence threshold:** Documented PEP responsibility to honor permit/deny, including denial before release.
- **Baseline verdict:** supported
- **C4\*+C6\* verdict:** supported
- **Proposed design verdict:** supported

#### `C6-OBLIGATIONS-ASSIGNED` — Apply masking/filtering before disclosure

- **Components:** C6
- **Source interaction:** C4 obligations → C6 enforcement (B §A R7; B Table C R7)
- **Why this is a criterion:** Permitted requests can still require restricted disclosure.
- **Evidence threshold:** Documented enforcement responsibility; actual execution is tested separately.
- **Baseline verdict:** supported
- **C4\*+C6\* verdict:** supported
- **Proposed design verdict:** supported

#### `C6-OBLIGATIONS-MECHANISM` — A mechanism that applies the restrictions

- **Components:** C6
- **Source interaction:** Appendix A Table A-0, C6 deployment column
- **Why this is a criterion:** Assigning the responsibility does not establish that a mechanism exists.
- **Evidence threshold:** A named C6 subcomponent performing masking or filtering, present in the assessed baseline.
- **Baseline verdict:** **unresolved**
- **C4\*+C6\* verdict:** supported
- **Proposed design verdict:** supported

#### `C15-SCOPE` — Retrieve only authorized FHIR scope

- **Components:** C15
- **Source interaction:** C6 → C15: scoped FHIR query/filter (B §A R7; B Table C R7)
- **Why this is a criterion:** Record retrieval must respect authorization limits.
- **Evidence threshold:** Documented FHIR scope/filter responsibility; compatibility with C6 assessed under I3.
- **Baseline verdict:** supported
- **C4\*+C6\* verdict:** supported
- **Proposed design verdict:** supported

#### `I1-REQUEST` — Supply inputs for access decisions

- **Components:** C6 ↔ C4
- **Source interaction:** C6 → C4: subject, resource, action, purpose; consent context (B §A R7; B Table C R7)
- **Why this is a criterion:** C4 cannot evaluate need-to-know without decision inputs.
- **Evidence threshold:** Flow identifies the necessary logical request attributes and their direction; exact API schema is not demanded.
- **Baseline verdict:** supported
- **C4\*+C6\* verdict:** supported
- **Proposed design verdict:** supported

#### `I2-RESPONSE` — Use a consistent decision/obligation contract

- **Components:** C4 ↔ C6
- **Source interaction:** C4 → C6: permit/deny + masking/date restrictions (B §A R7; B Table C R7)
- **Why this is a criterion:** C6 must interpret C4 restrictions and handle mandatory unenforceable ones.
- **Evidence threshold:** Evidence of shared obligation action/target/meaning and safe failure behaviour, from explicit contract or tested logical model; naming obligations alone is insufficient.
- **Baseline verdict:** **unresolved**
- **C4\*+C6\* verdict:** **unresolved**
- **Proposed design verdict:** supported

#### `I3-SCOPE` — Preserve authorized scope across retrieval

- **Components:** C6 ↔ C15
- **Source interaction:** C6 → C15: authorized query; C15 filters (B §A R7; B Table C R7)
- **Why this is a criterion:** Split enforcement must not expand allowed records, dates or fields.
- **Evidence threshold:** Evidence of allocated filter responsibilities and scope preservation through both components; selected tested contracts may support only the proposed model.
- **Baseline verdict:** **unresolved**
- **C4\*+C6\* verdict:** **unresolved**
- **Proposed design verdict:** supported

#### `I4-DATA` — Release only correctly restricted data

- **Components:** C6 ↔ C15
- **Source interaction:** C15 → C6 → client: filtered bundle returned (B §A R7; B Table C R7)
- **Why this is a criterion:** Later assembly/release must not undo masking/filtering.
- **Evidence threshold:** Evidence that all mandatory restrictions survive to final output and failed enforcement blocks disclosure.
- **Baseline verdict:** **unresolved**
- **C4\*+C6\* verdict:** **unresolved**
- **Proposed design verdict:** supported

#### `STATE-POLICY` — Identify policy-definition owner

- **Components:** C4 / C4.2
- **Source interaction:** C4.2 Policy Registry (A §A.0, Table A-0)
- **Why this is a criterion:** Policy evaluation needs an accountable owner for policy definitions.
- **Evidence threshold:** An explicitly named policy owner; does not by itself establish storage consistency.
- **Baseline verdict:** supported
- **C4\*+C6\* verdict:** supported
- **Proposed design verdict:** supported

#### `STATE-CONSENT` — Identify current consent-state owner

- **Components:** C4 / C4.2; C14 issues consent credentials
- **Source interaction:** Consent Manager role via C14 and C4.2; C4.2 holds current consent (A §A.0, pp. 2–3)
- **Why this is a criterion:** Need-to-know decisions use consent constraints.
- **Evidence threshold:** An explicit current-state owner and read responsibility; updates/synchronization assessed separately.
- **Baseline verdict:** supported
- **C4\*+C6\* verdict:** supported
- **Proposed design verdict:** supported

#### `STATE-REQUEST` — Decide whether persistent request/session state is required

- **Components:** C6
- **Source interaction:** Single-request R7 pilot; no multi-request session flow selected (B §A R7; B Table C R7; analyst-set scope)
- **Why this is a criterion:** Statefulness should be justified by required behaviour, not assumed for every gateway.
- **Evidence threshold:** Mark N/A only for this fixed single-request case; cannot infer the entire C6 service is stateless.
- **Baseline verdict:** n/a
- **C4\*+C6\* verdict:** n/a
- **Proposed design verdict:** n/a

#### `STATE-CONSENT-COORDINATION` — Decide whether mid-request consent updates must be coordinated

- **Components:** C4 ↔ C14
- **Source interaction:** Fixed consent snapshot in pilot (A §A.0 consent role; analyst-set scope)
- **Why this is a criterion:** Dynamic consent updates would require additional state/interface rules.
- **Evidence threshold:** Mark N/A only because consent updates are excluded; does not validate update propagation.
- **Baseline verdict:** n/a
- **C4\*+C6\* verdict:** n/a
- **Proposed design verdict:** n/a

### Supplementary criteria

#### `C5-AUDIT` — Record allowed and denied access

- **Components:** C5
- **Source interaction:** C6 → C5: permitted/denied action logged (B §A R7; B Table C R7)
- **Why this is a criterion:** The R7 flow explicitly names basic audit even though current direct-coverage boundary separates it.
- **Evidence threshold:** Documented audit role for permit/deny events; richer enforcement detail assessed separately.
- **Baseline verdict:** supported
- **C4\*+C6\* verdict:** supported
- **Proposed design verdict:** supported

#### `I5-AUDIT` — Transmit audit event information

- **Components:** C6 ↔ C5
- **Source interaction:** C6 → C5: audit handoff (B §A R7; B Table C R7)
- **Why this is a criterion:** Audit needs shared event contents between producer and receiver.
- **Evidence threshold:** Evidence of required event fields and C6/C5 responsibilities for decisions and enforcement outcomes.
- **Baseline verdict:** **unresolved**
- **C4\*+C6\* verdict:** **unresolved**
- **Proposed design verdict:** **unresolved**

#### `C5-ENFORCEMENT-OUTCOME` — Record applied or blocked restrictions

- **Components:** C5
- **Source interaction:** C6 enforcement → C5 audit (B §A R7; B Table C R7; strengthened assessor criterion)
- **Why this is a criterion:** An audit trail may need more than decision allow/deny.
- **Evidence threshold:** Explicit requirement/design evidence for applied-vs-blocked restriction records; not inferred from basic logging.
- **Baseline verdict:** **unresolved**
- **C4\*+C6\* verdict:** **unresolved**
- **Proposed design verdict:** **unresolved**

