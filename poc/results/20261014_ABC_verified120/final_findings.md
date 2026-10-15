# Final findings: English edition

## Findings

- B used 44.28% fewer search tokens than A, with six fewer correct answers and no median speed improvement. Candidate coverage was similar; sampled-source coverage fell. File coverage alone does not prove the required fact was read.
- All nine C reuse hits were wrong. A answered the same IDs with four correct, four no-results, and one wrong. C gained five correct answers on the other 111 questions, producing a net gain of one. This does not establish a reuse benefit.
- Reuse hits averaged 1.72 seconds and 201 tokens, versus A's 39.31 seconds and 100,261 tokens on those IDs. Across all questions, C used 16.64% fewer tokens but had a 2.70-second higher median.
- Seven hits involved predefined pairs; SVC-20 and CONS-07 were outside them. Wrong-version matches reached 0.994 and 0.993 similarity. The reuse function checks similarity and usable content, without a new factual-applicability check inside that function.
- No broad question was fully correct (13 per run). All nine negative questions received accepted refusals; this does not imply that other answers were factually correct.

## Limits and incidents

- A's Unicode export was repaired without rerunning search or grading. Original/fixed code hashes and the regression result are recorded.
- C/SVC-03 recovered through retry; 137.83 seconds and 148,219 tokens remain included. A/B/C had 5/2/3 serialization recoveries and no unrecovered runtime errors.
- Each stage had two direct-document routes with a separate five-file default. CONS-16 missed the ten named files. The legacy DOC's parsing corruption was retained across runs.
- SVC-15 has ambiguous audit scope. Excluding it gives 62.18% / 57.14% / 63.03%; main scores retain all questions.
- Scoring and secondary review were automated using the same configured service as search. All 190 required reviews were resolved. Initial and final decisions remain separate.
- Timing excludes preparation, scoring, review, and export. Usage includes successful sampling calls; failed calls may have unreported usage. The 128,000-token setting is not a strict cap.
- These are one-pass results on selected questions. C uses only earlier C clusters; identical-question replay and production-scale performance were not tested.

The campaign retains 360 responses and 238 clusters: A=82, B=76, C=80. Structural checks confirm unchanged source files, inputs, and recorded answers; they do not establish every semantic grade. See the methodology for full definitions.
