# Result tables

Three evaluation runs, all on the same items, prompts, judge (Qwen3.5-397B), temperature 0 and one sample per item:

| Run | Models |
|---|---|
| `paper-full-20260818-v1` | GLM-5.2, Kimi-K2.6, DeepSeek-V4-Pro, MiniMax-M2.5 |
| `midtier-20260828-v1` | DeepSeek-V3, GLM-4-32B-0414, Hunyuan-A13B, Ling-flash-2.0 |
| `intl-20260828-v1` | Gemini-3.7-Flash, GPT-5.6-Luna, Llama-4-Maverick |

The paper pools the eleven models; every number in it can be recomputed from the three `*.detail_scores.csv` files.

## `<run>.detail_scores.csv`, one row per model and item

| Column | Meaning |
|---|---|
| `model`, `qid`, `task_type`, `domain`, `difficulty` | Model name and item coordinates |
| `sample_id` | Always 0 (one sample per item) |
| `score` | The item score in [0, 1] as defined in the paper: exact match (T1), gated rubric mean (T2), rubric mean (T3), task success (T4) |
| `exclude_from_main` | True if the record could not be scored (none in the released tables) |
| `needs_review`, `warnings`, `problems` | Diagnostic flags recorded by the grader |
| `judgment_correct` | T2 only: whether the model's verdict matched the key (the gate) |
| `reason_score_normalized` | T2 only: mean of the four justification dimensions, kept even when the gate is 0 |
| `judge_repeats`, `judge_score_range`, `judge_all_identical`, `judge_dim_identical_fraction` | T2/T3 only: bookkeeping of the judge pass (one repeat in the main tables) |
| `t4_passed`, `t4_total`, `t4_functional_pass_rate`, `t4_meets_threshold`, `t4_performance_failed`, `t4_failure_class`, `t4_pass_at_1` | T4 only: per-case outcomes and the grader's failure class (`FUNCTIONAL_ASSERTION`, `RUNTIME_ERROR`, `PROCESS_CONSTRAINT`, `TAMPERING_REJECTED`, `SYNTAX_OR_IMPORT`, or `OK`) |
| `contamination_risk` | `flagged` if a phrase-match screen against the item's cited titles, or manual review, suggested the answer may be exposed through its source; not used in the paper |
| `run_id`, `paper_eligible` | Provenance; `paper_eligible` is True for every row |

## `<run>.summary_scores.csv`, one row per model, sub-domain, task type and difficulty cell

`n` items in the cell, `mean_score` with a bootstrap or Wilson 95 % interval (`ci_low`, `ci_high`), the T2 verdict accuracy (`t2_judgment_accuracy`) and the T4 task-success rate (`t4_pass_at_1`) where applicable.
