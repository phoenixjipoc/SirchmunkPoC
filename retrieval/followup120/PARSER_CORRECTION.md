# Parser comparison correction

The first P/P0 replay did not activate the repaired parser in live retrieval. It patched `_run_rga`, while the installed keyword tool calls `_run_rga_async`. The direct file probe succeeded, but that did not validate the integration. Both first-replay arms used the default parser. Their candidate sets were identical; native file order changed on 73 of 120 questions.

The original parser code and failed comparison are retained. Corrected P/P0 results use `parser_replay_corrected.py`, which wraps the actual asynchronous executor and records its arguments. A source-verified phrase is checked through the real keyword tool before the full replay: the legacy source must appear with the adapter and remain absent in the control. This is an integration check, not an additional benchmark question.

Both corrected arms use `--sort=path` to control file order. P alone adds the custom adapter. This is a controlled parsing diagnostic, not a proposed relevance-ranking method. Compare P with its matched P0 control; do not attribute differences from R1 to parsing alone. All 120 original questions, frozen keyword terms, directory outputs, raw files and acceptance rules remain unchanged. No new benchmark questions or remote retrieval requests are added.

The first source-check stage finishes before corrected replay starts. Its decisions remain reusable for identical question/source/criteria combinations. The final reference pool is rebuilt after corrected replay, and newly first-ranked sources receive a second check where necessary. Initial pool and failed parser records remain in `parser_initial_invalid`.
