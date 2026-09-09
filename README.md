# CESBench

A benchmark of 370 hand-written items for evaluating large language models on **cryptographic engineering security**: side-channel attacks, fault injection, secure implementation, countermeasures, security evaluation and certification, and the integration of cryptographic modules into IoT devices and other systems.

The benchmark is described in *CESBench: Benchmarking LLMs on Cryptographic Engineering Security for IoT Devices* (under review, 2026). This repository holds the items, the code tasks, the exact prompt templates, and the per-item score tables behind the paper's numbers.

## What is in the benchmark

| Sub-domain | Multiple choice | Judgment | Scenario | Code | Total |
|---|---:|---:|---:|---:|---:|
| D1 Side-channel attacks | 42 | 17 | 15 | 6 | 80 |
| D2 Fault injection | 30 | 8 | 8 | 4 | 50 |
| D3 Implementation | 44 | 15 | 14 | 7 | 80 |
| D4 Countermeasures | 33 | 11 | 10 | 6 | 60 |
| D5 Evaluation and certification | 30 | 8 | 8 | 4 | 50 |
| D6 Module integration | 30 | 8 | 8 | 4 | 50 |
| **Total** | **209** | **67** | **63** | **31** | **370** |

Four task types test different competences:

- **T1 Multiple choice** tests recall. One correct option, three distractors written from documented practitioner misconceptions.
- **T2 Judgment** tests whether the model can defend a security verdict. The model answers True or False and justifies it; a wrong verdict scores zero, a correct one is scored on four rubric points.
- **T3 Scenario** tests engineering diagnosis. The model works through a concrete situation and is graded against a rubric of three to five equal-weight dimensions.
- **T4 Code** tests implementation. The model writes a Python function that is graded by 414 pytest cases across the 31 tasks, with process checks that reject shortcut implementations.

## Files

| Path | Contents |
|---|---|
| `CESBench-EN-v20260902.xlsx` | The 370 items. Sheets `T1-MCQ`, `T2-TrueFalse`, `T3-Scenario`, `T4-Code` hold the items, answers, justifications, rubrics, sources and authorship; `00-Overview` gives the counts. |
| `code_tasks/<item id>/` | One folder per code task: `problem.md` (the statement shown to the model), `metadata.json` (the fields that enter the prompt and the test count), `test.py` (the graded pytest suite), `solution.py` (a reference implementation). |
| `prompts/prompts.py` | The prompt templates used for every task type, for the answering model and for the judge, exactly as run. Standalone: `t1_prompt`, `t2_answer_prompt`, `t2_judge_prompt`, `t3_answer_prompt`, `t3_judge_prompt`, `t4_prompt`. |
| `results/` | Per-item scores of the eleven evaluated models, one row per model and item, plus per-cell summaries. See `results/README.md` for the columns. |

### Item fields

- Every item carries `id` (`D<sub-domain>-T<task>-<number>`), `domain`, `difficulty` (`Basic` / `Intermediate` / `Expert`, the authors' judgment), `sub_topic`, `source`, `author`, `reviewed_by`, `version`, `last_updated`.
- T1: `question`, `option_a` to `option_d`, `answer`, `justification`.
- T2: `statement`, `answer` (True / False), `justification`, `scoring_rubric` (the four rubric points).
- T3: `scenario`, `task`, `rubric` (the graded dimensions), `max_score` (the number of dimensions), `passing_threshold`, `expert_criteria` (background for the judge, never a basis for deducting marks), `reference_answer`.
- T4: `function_signature`, `constraints`, `expected_pass_rate`, and links into `code_tasks/`.

## Scoring

- **T1**: exact match on the answer letter.
- **T2**: the four rubric dimensions are each awarded 0, 0.5 or 1 by an LLM judge and averaged; the result is multiplied by the verdict gate, 1 if the model's verdict matches the key and 0 otherwise. The dimension scores are kept so that verdict accuracy and justification quality can be reported separately.
- **T3**: the mean of the rubric dimensions, each awarded 0, 0.5 or 1 by the judge.
- **T4**: task success, 1 when every functional test passes and no process check fails, otherwise 0. A syntax error, a runtime error or a timeout also scores 0. Process checks catch shortcuts such as calling a prohibited library primitive instead of implementing the algorithm; they assume non-adversarial submissions.
- **Composite**: the unweighted mean of the four task-type scores.

In the paper the judge is Qwen3.5-397B, a model family disjoint from the evaluated models; its scores were checked against a repeat pass, a second judge (Grok-4.6), and blind human re-scoring.

## Notes

- The workbook is edition v20260902. The evaluation runs were anchored to edition v20260807, which differs from it only in the `reviewed_by` column and the version stamp on the `00-Overview` sheet.
- Items are bound to specific standard editions, library versions and dates and will need review as those change.
- The evaluation pipeline, the archived model responses and judge outputs will be released with the published paper.

## Citation

The paper is under review. Until it appears, please cite this repository:

```
Wenquan Zhou, An Wang, Jing Liang, Peien Feng, Jingqi Zhang, Yaoling Ding, and Liehuang Zhu.
CESBench: Benchmarking LLMs on Cryptographic Engineering Security for IoT Devices. 2026.
https://github.com/wenquan222/CES
```

## License

- The benchmark data, that is the workbook, the code-task statements and metadata, the rubrics and the result tables, is released under the Creative Commons Attribution 4.0 International license (`LICENSE`).
- The code, that is `prompts/prompts.py` and the `test.py` and `solution.py` files under `code_tasks/`, is released under the MIT license (`LICENSE-CODE`).

Please attribute by citing the paper or this repository.

## Contact

Wenquan Zhou, Beijing Institute of Technology. Corresponding author: Yaoling Ding (dyl19@bit.edu.cn).
