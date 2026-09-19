---
name: image-factory-judge
description: Use when a batch has been generated and its results need a verdict, when the user asks whether a batch came out right, or when the results should be turned into another round. Runs the deterministic gates, records any advisory score next to the human labels so the two can later be compared, and writes the next round's plan from the items that actually need rework. Use when the user says "check these", "score the batch", or "try again with better prompts". For producing the images in the first place use `image-factory-run`.
---

# Evaluate and optimize a batch

## When to use

Use this skill after a batch has generated receipts or definite terminal
failures. Its job is to answer two separate
questions and keep them separate: whether the artifacts are sound, and whether
they are what the user wanted.

Do not use it to generate images. It never spends the account's allowance.

## Workflow

Read and follow
[the self-contained conversation workflow](references/conversation-workflow.md)
when presenting numbered results and interpreting whole-batch, partial, or
single-image decisions. Preserve the user's exact adjustment words as the reason
for a rewrite.

1Step 1. **Look at the results yourself before scoring them.** Read the generated
   images and compare them with what the plan asked for. This is the part Codex
   is genuinely needed for: judging whether a picture matches the intent.

2Step 2. **Run the deterministic gates.**

   ```bash
   bin/image-factory evaluate --plan plan.json --job job.json --scores scores.json \
     --destination out/ --json
   ```

   These gates have exactly one true answer each: a file exists, it is a PNG, it
   meets the minimum dimension, its hash matches the receipt, and the same image
   is not standing in for two different items. A failure here is a real failure.

   Current rows in `Failed` and `Skipped` are definite outcomes. They may be
   evaluated without receipts and receive the deterministic `missing_artifact`
   failure. A current `Unknown`, `Pending`, or `Attempting` row is not evaluable:
   reconcile ambiguity first and stop if `Unknown` remains. Receipt evidence on
   a `Failed` or `Skipped` row is contradictory and must be rejected.

3Step 3. **Record your own assessment as advisory, and say that it is advisory.**

   ```bash
   bin/image-factory evaluate ... --advisory advisory.json --json
   ```

   The advisory file maps an item id to `[score, reason]` with the score between
   0 and 1. Write a concrete reason: "the key light comes from the wrong side"
   is useful to a rewrite; "not great" is not.

   Be explicit with the user that a model-produced score is recorded as a
   signal, not as a verdict. It is compared against `pass_threshold` only to
   decide whether a person needs to look, and it is never allowed to fail a
   batch on its own. The reason is practical: if the same model wrote the prompt
   and then scored the result, refining against that score converges on what the
   scorer likes rather than on what the user asked for.

4Step 4. **Capture the user's decision, and let it outrank your score.** Record
   `approved` or `rejected` per item in the labels file. A human rejection fails
   the batch even when every gate passed and your score was perfect. These
   labels are the calibration data for the advisory signal, so record them even
   when they contradict your own assessment.

   Accept natural language such as `整组批准`, `批准 1、2、4`, `第 3 张改成更温暖`,
   or `全部换一种风格`. Map visible numbers back to item ids. Unmentioned items
   remain unlabeled; never infer approval from silence.

   When required labels remain missing, describe `PendingApproval` as waiting
   for the user's decision, not as failure. Only a fully approved passing batch
   becomes `Accepted`.

5Step 5. **Turn the failures into the next round.** Decide what to change for each item
   that needs rework, then hand those decisions to the optimizer:

   ```bash
   bin/image-factory optimize --job job.json --plan plan.json --scores scores.json \
     --rewrites rewrites.json --out next-round.json --json
   ```

   `rewrites.json` maps an item id to a new prompt. Use
   `--retry-unchanged item-id` for an item whose prompt was fine and whose
   failure was environmental. Every item that needs rework must be given one or
   the other: an instruction cannot be left implicit.

   A definite failed item is never retried merely because evaluation found it.
   After the job enters `Evaluated`, require either an explicit rewrite or an
   explicit `--retry-unchanged` decision before creating the next round.

   Write rewrites that name the difference you observed, not a general
   instruction to do better. If the palette came out too saturated, say which
   colours should dominate.

6Step 6. **Validate the plan for the next round before anyone runs it.**

   ```bash
   bin/image-factory validate-plan next-round.json --json
   ```

   Then report the decision and the carried-forward items. An item that already
   passed is not regenerated, so the next round is smaller than the last.
   Optimization changes the plan and invalidates the prior approval. Show a new
   confirmation card, quote the exact remaining calls for that round, and obtain
   a new approval before generation.

## Platform boundaries

A rewrite can change the prompt and the reference images. It cannot change
anything else: size, quality, background, and image count are fixed by the
built-in tool. Never promise the user a size or a quality tier in a rewrite, and
never write a prompt whose intent depends on those settings.

## Inputs

- The plan for the round that was generated.
- The job ledger and the receipts from `image-factory-run`.
- Optional advisory scores and human labels.

## Outputs

- A scores document conforming to `schemas/scores.schema.json`, with
  `decision` set to `pass`, `fail`, or `pending_approval`.
- A next-round plan conforming to `schemas/image_batch.schema.json`, written only
  when something needs rework.

## Errors

- `optimizer_missing_instruction` — an item needs rework and was given neither a
  rewrite nor an explicit retry-unchanged. Decide, then rerun.
- `optimizer_round_cap_reached` — the plan's `max_rounds` is exhausted. This is
  reported as incomplete, never as success, and the remaining items are left for
  a human.
- `optimizer_ambiguous_instruction` — an item was given both a rewrite and a
  retry-unchanged. Choose one.

## Gotchas

- A perfect advisory score does not survive a human rejection. If you recorded a rejection, the batch fails.
- Recording no advisory score at all is legitimate. A made-up number is worse than an empty one, because it looks like evidence.
- Do not rewrite a prompt for an item you never looked at. Open the image first.
- A low advisory score asks for a human; it does not fail the batch. Do not describe `pending_approval` to the user as a failure.
- Reaching the round ceiling is reported as incomplete. Do not present it as a finished job.
- The previous round's plan is immutable. If you edited it in place, the round number no longer links a result to its instruction.
- An environmental failure (timeout, missing artifact) does not need a new prompt. Use the explicit retry-unchanged instruction so the decision is visible.

## Never do

- Never present an advisory score as the verdict, and never let it override a
  human rejection.
- Never edit the previous round's plan. A new round is a new document, and the
  round number links a result back to the instruction that produced it.
- Never invent a rewrite for an item you did not look at.
- Never regenerate an item that already passed.
- Never turn a definite failure into an implicit retry.
- Never treat reaching the round ceiling as a success.

<!-- QUALITY_BASELINE_V1 -->
## When to use（什么时候使用）

当用户需要 **基于可验证证据进行质量、安全或交付审查** 时加载本技能。先从请求中提取目标、输入、约束、交付格式和验收标准；描述摘要为：Use when a batch has been generated and its results need a verdict, when the user asks whether a batch came out right, or when the results should be turned into another round. Runs the deterministic gates, records any advisory score next to the human labels so the two can later be compared, and writes the next round's plan from the items that actually need rework. Use when the user says "check these", "score the batch", or "try again with better prompts". For producing the images in the first place use `image-factory-run`.。

## Rules

- 先读后写：先确认当前状态与真实能力，再执行会改变外部状态的动作。
- 权限最小化：只使用完成当前步骤所需的文件、工具、账户与网络范围。
- 证据优先：运行结果、资源 ID、版本、哈希或测试输出缺失时，明确标记为 `NOT_VERIFIED`。
- 幂等优先：保留请求标识与阶段状态；结果不明确时先查询，不进行盲目重试。
- 隐私安全：日志、示例、回执和错误信息不得包含 token、cookie、密钥或个人敏感数据。

## Workflow

### Step 1：澄清意图

确认本技能是否匹配目标；若只是相邻需求，交给更精确的技能。
### Step 2：执行预检

冻结审查对象、验收标准、证据时间和版本标识；任一关键条件未知时停止在只读阶段。
### Step 3：形成计划

列出将调用的工具、会改变的对象、成功标准以及失败后的安全退出方式。
### Step 4：执行动作

逐项判定 PASS、FAIL、SKIPPED 或 BLOCKED，并记录依据；每个外部调用均保留可关联的状态或回执。
### Step 5：验证交付

输出发现、严重度、证据位置、修复建议和剩余风险，并把事实、推断和未验证项分开陈述。

## Validation checklist

- [ ] 技能触发条件与用户意图一致，没有把相邻任务误路由到本技能。
- [ ] 输入、目标对象、版本和输出位置均已明确，且没有使用猜测值替代必填值。
- [ ] 所有写入、付费、发布或不可逆动作都在用户授权范围内。
- [ ] 结果已用独立检查验证；仅有“命令成功”或“文件存在”不算完整验收。
- [ ] 输出包含实际证据、失败/跳过项、剩余风险和可执行的下一步。

## Gotchas

1. **把计划当结果**：文档或提示词不等于真实执行；必须标明实际运行层级。
2. **错误重试**：超时或响应丢失可能已经产生远端状态，先查询再决定是否重试。
3. **隐式扩大范围**：批量、全量、发布、覆盖和付费不是普通读写的自然延伸。
4. **版本漂移**：引用外部资源时记录版本、tag 或提交；不要把可变分支当发布证据。
5. **证据过期**：缓存、旧截图和历史测试不能证明当前环境；在交付前刷新关键证据。

## 不适用与边界

审查结果不是修改授权；不伪造运行证据，也不把缺失证据标为通过。 如果请求需要别的技能，不复制其正文；按技能名称进行交接，并保留当前任务上下文。

## Progressive disclosure

- 需要确定输入/输出、状态和授权点时，读取 `references/workflow-contract.md`。
- 需要交付前自检时，读取 `references/validation-checklist.md`。
- 遇到超时、部分成功或恢复场景时，读取 `references/error-recovery.md`。
- 首次运行、拒绝越权和失败恢复分别参考 `examples/happy-path.md`、`examples/boundary-refusal.md`、`examples/failure-recovery.md`。
