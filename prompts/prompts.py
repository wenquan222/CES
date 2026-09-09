"""English-native prompt templates for CESBench.

The English bank is the final deliverable; the Chinese bank is frozen archive
(tag ``v7.2-zh-frozen``). The previous all-Chinese templates are preserved
verbatim in ``prompts_zh_archive.py`` so that the historical Chinese runs stay
reproducible -- they are no longer used by the runners.

Why this file had to be rewritten: with Chinese instructions wrapped around
English questions, the evaluation measured a *mixed-language* task. Ability to
follow Chinese instructions and to switch languages leaked into what was
reported as cryptographic-engineering ability. Every string a model or a judge
sees is now English.

Two long-standing scoring defects are also fixed here, because both live in the
prompt rather than in the bank:

1. ``expert_criteria`` reaches the T3 judge. Several items ask the answer to
   cite a specific paper, source file or commit hash -- material a model cannot
   retrieve. Left as-is it penalises correct answers and rewards fabricated
   citations. The judge is now told explicitly that this field is background
   only and must never be a basis for deducting marks.
2. The T2 truth convention (a compound statement is False if *any* part is
   wrong; an incomplete set of necessary conditions is False) was applied by the
   reference answers but never stated to the model. It is now stated.
"""

from __future__ import annotations

from typing import Any

def _common_dimension_ids(n: int) -> list[str]:
    """Canonical dimension ids d1..dN in rubric order (standalone copy of the pipeline helper)."""
    return [f"d{i}" for i in range(1, int(n) + 1)]


def t1_prompt(q: dict[str, Any]) -> str:
    return f"""You are an expert in cryptographic engineering security.
Answer with exactly one letter -- A, B, C or D. Do not explain, do not restate
the question.

Question:
{q.get("question")}

A. {q.get("option_a")}
B. {q.get("option_b")}
C. {q.get("option_c")}
D. {q.get("option_d")}

Answer (one letter only):"""


def t2_answer_prompt(q: dict[str, Any]) -> str:
    return f"""You are an expert in cryptographic engineering security. Decide
whether the statement below is True or False, and give a concise but
well-grounded reason.

Statement:
{q.get("statement")}

How to decide True vs False:
- A statement counts as True only if it is correct **as a whole**. If it is a
  compound claim and any part of it is wrong, answer False.
- If the statement presents a set of conditions as sufficient but the set is
  incomplete, answer False.
- Judge the claim as written. Do not repair it into a weaker claim that would
  be true.

Output requirements:
1. "judgment" must be exactly "True" or "False".
2. "reason" must be in English and state the decisive grounds.
3. Output strict JSON only. No Markdown.

Output format:
{{"judgment": "False", "reason": "your reason here"}}"""


def _reasoning_rubric_only(rubric: str) -> str:
    """去掉 rubric 开头的 `[Verdict gate] ...` 段，只留理由维度。

    第七轮指出的矛盾：prompt 明写「不告诉你参考答案，也不要推断」，而传进去的
    rubric 第一句就是「若模型判断与**参考答案**不一致则本题 0 分」——盲化被
    rubric 自身抵消了。67 道 T2 的这段前缀完全一致，止于 `[Reasoning:`。

    verdict gate 本就由代码 exact-match 执行，judge 不需要看见它。
    找不到标记时原样返回：宁可少删，也不要把理由维度一起切掉。
    """
    text = str(rubric or "")
    if not text.startswith("[Verdict gate]"):
        return text
    marker = "[Reasoning:"
    idx = text.find(marker)
    return text[idx:] if idx != -1 else text


def dimension_ids(n: int) -> list[str]:      # noqa: F811 —— 转发给 common 的唯一定义
    """维度的稳定身份：`d1..dN`，按 rubric 里的出现顺序。

    第八轮 P1-3：靠**名字**认维度是不可靠的——judge 可以返回五个同名维度、
    可以用 Unicode 同形字（拉丁 `i` / 西里尔 `і`）绕过查重、调换顺序还会让
    重复判分的一致率算错。

    这里不去解析 rubric 散文（实测行首锚定在 85/130 道上失效：多数题把维度
    写在同一行用分号隔开，而圈码 ①② 又会在正文里被引用），而是利用一个更
    结实的事实：**维度是有序且有数的**，`max_score` 就是维度数，门禁一直在
    校验这一点。所以 ID 直接由序号决定，judge 只需按 rubric 顺序逐一对应。

    好处是身份与可编辑的标题彻底脱钩——Codex 明确警告过不要拿标题当 ID。

    **唯一定义在 `common.dimension_ids`**，这里只做转发：第九轮要求
    prompt 与两个 grader 共用同一份规范，不能各自复制一份 `d1..dN`。
    """
    return _common_dimension_ids(n)


def _dimension_example(n: int) -> str:
    """输出格式示例必须**列满 N 维**。

    第九轮 P0-2：T3 的示例原先只写一个 `d1`，而前文要求「返回每个 ID」。
    裁判照着示例只回一维时，旧代码按 1/max_score 等比例给分还进主均值。
    示例是最强的指令——不能和正文说的不一致。
    """
    rows = []
    for i, did in enumerate(dimension_ids(n), start=1):
        score = (0.5 if i == 1 else (1 if i % 2 else 0))
        rows.append(f'    {{"id": "{did}", "name": "short label for dimension {i}", '
                    f'"score": {score}, "reason": "grounds for this score"}}')
    return ",\n".join(rows)


def _dimension_instruction(n: int) -> str:
    ids = dimension_ids(n)
    return (
        f"The rubric defines exactly {n} dimensions, in the order they appear. "
        f"Return one entry per dimension, tagging them {', '.join(ids)} in that "
        f"same order. The `id` field is what identifies a dimension -- the `name` "
        f"field is a human-readable label only and is never used for matching. "
        f"Return every id exactly once: no omissions, no duplicates, no other ids."
    )


def t2_judge_prompt(q: dict[str, Any], model_judgment: str, model_reason: str) -> str:
    return f"""You are an expert reviewer in cryptographic engineering security.
You are grading the quality of a model's reasoning on a true/false item.

Item ID:
{q.get("id")}

Statement:
{q.get("statement")}

Scoring rubric (the ONLY basis for marks):
{_reasoning_rubric_only(q.get("scoring_rubric"))}

Model reasoning:
{model_reason}

Score the reasoning along the 4 rubric dimensions. Each dimension takes only
0, 0.5 or 1:
- 0   -- not met: missing, or plainly wrong.
- 0.5 -- partially met: relevant but incomplete, or with a minor error.
- 1   -- met: the key point is correct and sufficiently supported.

Rules:
1. **You are not told the reference verdict, and you must not try to infer it.**
   Grade the reasoning against the rubric alone. Whether the model's verdict was
   right is decided separately by exact match in code, and the verdict gate is
   applied there -- knowing the answer here would only anchor your scoring.
2. {_dimension_instruction(4)}
3. Grade only what the model actually wrote. Do not complete its argument for it.
4. Output strict JSON only. No Markdown.

Output format:
{{
  "dimensions": [
    {{"id": "d1", "name": "short label", "score": 0, "reason": "grounds for this score"}},
    {{"id": "d2", "name": "short label", "score": 0.5, "reason": "grounds for this score"}},
    {{"id": "d3", "name": "short label", "score": 1, "reason": "grounds for this score"}},
    {{"id": "d4", "name": "short label", "score": 1, "reason": "grounds for this score"}}
  ],
  "judge_reason": "overall assessment"
}}"""


def t3_answer_prompt(q: dict[str, Any]) -> str:
    return f"""You are an expert in cryptographic engineering security. Work
through the scenario below and give a complete, actionable answer.

Scenario:
{q.get("scenario")}

Task:
{q.get("task")}

Requirements:
1. Cover the key causes, the grounds for your judgement, and the verification
   steps or mitigations.
2. Structure the answer clearly. Do not output JSON.
3. Do not pad with generic advice unrelated to this scenario."""


def t3_judge_prompt(q: dict[str, Any], model_response: str) -> str:
    return f"""You are an expert reviewer in cryptographic engineering security.
Score the model's scenario answer dimension by dimension against the rubric.

Item ID:
{q.get("id")}

Scenario:
{q.get("scenario")}

Task:
{q.get("task")}

Scoring rubric (the ONLY basis for marks):
{q.get("rubric")}

max_score:
{q.get("max_score")}

passing_threshold:
{q.get("passing_threshold")}

Model answer:
{model_response}

Scoring rules:
1. Score each rubric dimension independently.
   {_dimension_instruction(q.get("max_score") or 0)}
2. A dimension takes only 0, 0.5 or 1 -- no other value, and no weights. The
   totals are computed in code from the bank's own structure; anything you
   report beyond the per-dimension scores is ignored.
3. Award marks only for what the answer states explicitly or directly implies.
   Do not complete the argument on the model's behalf.
4. Do not deduct marks for the absence of a citation to a specific paper,
   source file, function name or commit hash. The model cannot retrieve that
   material, and rewarding it would reward fabricated citations.
5. Output strict JSON only. No Markdown.

Output format:
{{
  "dimensions": [
{_dimension_example(q.get("max_score") or 0)}
  ],
  "judge_reason": "overall assessment"
}}"""


def t4_prompt(task: dict[str, Any], required_imports: list[str]) -> str:
    metadata = task["metadata"]
    constraints = metadata.get("constraints", [])
    constraints_text = (
        "\n".join(f"- {item}" for item in constraints)
        if isinstance(constraints, list)
        else str(constraints)
    )
    imports_text = (
        "\n".join(f"- `{item}`" for item in required_imports)
        or "- the function named in the problem statement"
    )
    return f"""You are a senior Python / NumPy engineer. Complete one
HumanEval-style coding task.

Requirements:
- Output one complete Python source file and nothing else. No Markdown, no
  explanation.
- You must define the function named in the problem statement. Helper constants
  and helper functions are allowed.
- The tests import the following objects from `solution.py`; all of them must be
  defined:
{imports_text}
- Do not read files, do not access the network, do not write to stdout/stderr.
- Follow the stated constraints, especially the performance limits and the
  banned APIs.

Item ID: {metadata.get("id")}
Function signature: {metadata.get("function_signature")}
Difficulty: {metadata.get("difficulty")}
Topic: {metadata.get("sub_topic")}

Constraints:
{constraints_text}

Problem statement:
{task["problem"]}"""
