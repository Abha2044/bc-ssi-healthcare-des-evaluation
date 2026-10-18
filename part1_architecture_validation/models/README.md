# Models — the inputs

Nothing here is a result. Every file is either a transcription of a source
document or an explicitly recorded judgement.

| File | Holds | Comes from |
|---|---|---|
| `requirements.json` | what each requirement needs, with no component named | Appendix B, Table C — capability-goal column |
| `components/C*.json` | one file per component: subcomponents, behaviours, interfaces, state | Appendix A, Table A-0 |
| `components/_order.json` | the component list; the loader fails if a file is missing | — |
| `_conventions.json` | shared rules that apply to every component file | — |
| `flows.json` | which components interact, in what order, for R7 | Appendix B, Table C — runtime-flow column |
| `capability_mappings.json` | which component behaviour is *claimed* to serve which capability, and the evidence for the claim | analyst, citing A and B |
| `r7_reference_assessment.json` | the 16 checks and a recorded verdict for each | analyst |
| `refined_variations.json` | what C4\* and C6\* change | Appendix A, Tables A-11 to A-13 |
| `proposed_contracts.json` | a proposed I2 payload and its test cases | proposed, not from any source |

Requirements name no components; components name no requirements. They are
joined only in `capability_mappings.json`, where every join carries a citation.

## Editing a component

Edit `components/C6.json` on its own. To add a component, add the file **and**
add its ID to `components/_order.json` — the loader refuses to run if the two
disagree, so a forgotten entry fails loudly instead of silently dropping a
component.
