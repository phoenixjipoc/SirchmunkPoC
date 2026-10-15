# Evaluation workflow and grading

## From question to answer

1. The harness submits an ID and question to `AgenticSearch.search()` in Docker, using DEEP mode. References are withheld.
2. C checks its own earlier clusters for reuse at similarity 0.85. The recorded function checks similarity and usable content, without a new factual-applicability check inside that function. A/B disable reuse.
3. Fresh search derives keywords and uses `rga` to locate candidate files and passages.
4. Kreuzberg extracts candidate text. Evidence sampling examines relevant portions of up to ten files in A/C or five in B. A few direct-document requests follow a separate five-file default.
5. Evidence is summarized into a cluster and answer, or the system returns no result. Clusters are saved for possible later reuse in C.
6. The harness records answers, sources, reuse, timing, usage, and errors. Scoring and review follow before export.

The same 120 questions produce 360 responses across A/B/C. Each stage starts with an empty cluster store. C does not reuse A/B clusters or repeat identical questions.

## Acceptance criteria

The [frozen question CSV](../poc/results/20261014_ABC_verified120/inputs/questions.csv) contains:

| Field | Purpose |
|---|---|
| `gold_answer` | Final reference answer |
| `gold_source_file` / `gold_passage` | Source filenames and evidence |
| `verify_note`, after `Acceptance:` | Required facts, allowed wording, optional details, and exclusions |
| `verify_answer` | Initial blind answer; may contain subsequently corrected mistakes |

All 120 questions have acceptance criteria fixed before testing. For INV-01, ten copies suffice; the template address is optional. For INV-03, up to ten clients with assets greater than $1 billion is required; exactly ten or at least $1 billion is not equivalent.

The [judge script](../poc/results/20261014_ABC_verified120/inputs/scripts/judge.py) compares the full response with the reference, evidence, and acceptance criteria by meaning, not exact wording.

## Scoring and review

| Label | Meaning | Correct? |
|---|---|---|
| `correct` | Required facts correct, with no contradiction | Yes |
| `correct_refusal` | Appropriate refusal on a negative question | Yes |
| `partial` | Required content missing | No |
| `wrong` | Wrong fact/document or unjustified refusal | No |
| `hallucinated` | Unsupported concrete answer on a negative question | No |
| `no_answer` | Fixed no-results response | No |
| `error` | Unrecovered execution failure | No |

Scoring is automated and uses the same configured service as search. The required review queue contained 190 records: initially non-correct answers plus about 20% of correct/refusal answers. Secondary review withheld initial labels; mechanical checks and source adjudication resolved the queue. Original and final decisions remain separate. No human sign-off was performed.

**Accuracy = (correct + correct_refusal) / 120.** A/B/C scored 74/68/75 correct, including nine correct refusals each: **61.67% / 56.67% / 62.50%**. All nine C reuse hits were wrong.

Reference verification and answer scoring are separate checks. Supporting or correcting a reference does not establish that the system answered the question correctly.
