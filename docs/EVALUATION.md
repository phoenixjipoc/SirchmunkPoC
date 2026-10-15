# Evaluation workflow and grading

This guide follows one question through the recorded 120-question A/B/C campaign. See [methodology](METHODOLOGY.md) for configuration and limitations, and the [execution history](../poc/results/20261014_ABC_verified120/test_process.md) for actual events.

## From question to answer

1. The host harness reads the frozen question order and invokes the container-side Python runner with `docker exec`. Search receives the question ID and question text, without the reference answer or acceptance criteria.
2. The runner calls `AgenticSearch.search()` in DEEP mode. C can reuse a suitable earlier cluster from C's own initially empty store; A and B disable reuse. C's similarity threshold is 0.85. The recorded reuse function checks similarity and nonempty content; it does not perform a new factual-applicability check inside that function.
3. On the main fresh-search path, the model interprets the question and derives search terms. `rga` searches extracted document text to find candidate files and matching passages.
4. Up to 10 candidate files in A/C, or five in B, enter evidence sampling. Kreuzberg extracts candidate text, and Monte Carlo evidence sampling selects and evaluates relevant portions. Selecting a file does not mean that the model reads its entire content. A few questions take a direct-document route with a separate five-file default.
5. Evidence is synthesized into a knowledge cluster and an answer with source information. The system can instead return no result. New clusters are saved; later C questions may reuse them. A cluster reuse hit uses existing content and can bypass fresh document search.
6. The harness saves the answer, candidate and evidence traces, citations, reuse identifiers, elapsed search time, token usage, warnings, and errors.
7. The answer is graded against the frozen reference, supporting passage, and acceptance criteria. Required reviews are resolved before final scores and exports are produced.

The same 120 questions run once in each stage, producing 360 answer records. C does not receive A/B's clusters or repeat an identical question within its own stage. Shared parsed-text cache is separate from knowledge-cluster memory.

## References and acceptance criteria

The exact grading inputs are in [the frozen question CSV](../poc/results/20261014_ABC_verified120/inputs/questions.csv). The matching [verified question table](../poc/questions/questions_verified.csv) is the readable master snapshot.

| Field | Role |
|---|---|
| `gold_answer` | Adjudicated reference answer |
| `gold_source_file` | One or more source filenames; empty for the nine negative questions |
| `gold_passage` | Supporting source text |
| `verify_note`, after `Acceptance:` | Required facts, allowed wording, optional details, and unacceptable interpretations |
| `verify_answer` | Initial independent blind answer, preserved even where later adjudication found a mistake |

All 120 questions have acceptance criteria. These were recorded during the independent source audit before the campaign. For INV-01, ten proposal copies suffice; a template address is optional. For INV-03, the required meaning is up to ten client references, each with assets greater than $1 billion; exactly ten or at least $1 billion is not equivalent. For XD-20, a response should say that no minimum pass score is specified, rather than invent a GRESB cutoff.

The [frozen judge script](../poc/results/20261014_ABC_verified120/inputs/scripts/judge.py) extracts the acceptance text and supplies it with the question, complete system answer, reference answer, and supporting passage. Its judgment is semantic rather than exact-string matching.

## Labels, reviews, and final accuracy

| Final label | Meaning | Counts as correct? |
|---|---|---|
| `correct` | Required facts are correct without a contradicting claim | Yes |
| `correct_refusal` | Appropriate refusal on a negative question | Yes |
| `partial` | Some required facts are correct, but required content is missing | No |
| `wrong` | Incorrect key fact, wrong document, or an unsupported refusal on an answerable question | No |
| `hallucinated` | A concrete unsupported answer on a negative question | No |
| `no_answer` | The recorded fixed no-results response | No |
| `error` | An unrecovered execution failure | No |

The primary judge used the same configured `gpt-5.4` model as search. Initially non-correct results and a reproducible approximately 20% sample of initially correct/refusal results formed a required review queue of 190 records across A/B/C. Secondary model review withheld the primary label; exact no-results/errors were checked mechanically. Coordinating AI review resolved disagreements and examined additional cases, including every reuse hit. Primary labels, secondary reviews, and final decisions remain separately recorded.

**Final accuracy = (correct + correct_refusal) / 120.** Partial answers and unsuccessful cases stay in the denominator. The final counts are A=74/120 (61.67%), B=68/120 (56.67%), and C=75/120 (62.50%). These include nine correct refusals in each run. All nine actual C reuse hits were wrong, so overall accuracy and reuse accuracy must be examined separately.

The independent question audit and the response evaluation are different checks. Source verification supported 109 original references and corrected 11; it did not establish that Sirchmunk answered those questions correctly. Both reference verification and answer grading rely on AI review, with recorded evidence and adjudication, and are not human certification.
