---
name: image-factory-use
description: Use when the user wants to produce a batch of images, run an image production round, or continue an image batch that already exists. Routes to `image-factory-run` for a batch that has not been generated yet, to `image-factory-judge` for a batch with results to evaluate or a next round to plan, and to `image-factory-recover` for a batch whose state is unclear or that was interrupted. This skill only picks the entry point and never performs the work itself. For a single ad-hoc image with no batch plan, no skill in this plugin applies — ask Codex for the image directly.
---

# Image Factory

## When to use

Use this skill as the entry point when a request touches image production as a
batch rather than as one picture: the user has several prompts, a reference
style to reproduce across variants, or an existing job they want to continue.

Do not use it to generate one image on request, to design a UI, or to edit a
document.

## Workflow

The conversation is the product surface. Read and follow
[the conversation workflow](references/conversation-workflow.md) so goal capture,
choices, generation approval, result labels, and later rounds use one contract.
Treat approval as transactional: it applies only to the displayed plan, round,
and remaining generation-call count. Any change invalidates it and requires a
new confirmation card and explicit approval.

For a new goal without a plan, the first user-facing response must advance the
work instead of returning only questions. Infer a sensible default and show:

```text
推荐方案：温柔母婴科普，6 张系列知识卡，人物与配色保持一致
可选方向：1. 温柔插画（推荐）  2. 专业信息图  3. 极简生活方式
回复“按推荐继续”，或直接修改方向、张数、文字、参考图。
```

Match the user's language and topic. Show at most three directions. 不能只回复问题；
when a missing fact materially changes the result, give the recommended default
first and ask one focused follow-up.

Step 1. Establish whether a batch plan already exists. Look for a plan file the
user named, or for a job ledger left by an earlier round.

Step 2. Classify the request into exactly one of three situations:

- **Nothing has been generated yet, including requests needing prompt inspiration or a batch plan.** Delegate to `image-factory-run`; its prompt preparation reference covers template search and series consistency.
- **Results exist and need a verdict, or need another round.**
  Delegate to `image-factory-judge`.
- **The state is unclear, a run was interrupted, or the user is asking what
  happened.** Delegate to `image-factory-recover`.

Step 3. State which situation you detected and why, then delegate. The delegate
continues the same conversation; the user never has to re-enter confirmed choices.

## Routing table

| Situation | Signal | Delegate |
| --- | --- | --- |
| New batch | A plan describing items, no ledger yet | `image-factory-run` |
| Verdict or next round | A ledger in `Completed`, `Partial`, or `Evaluated` | `image-factory-judge` |
| Unclear or interrupted | A ledger in `Running` or `Unknown`, or the user asks what happened | `image-factory-recover` |

## Gotchas

- A ledger without a plan file is not a dead end: the ledger records what was attempted, so recover the state first and ask the user for the plan only if a resume is actually needed.
- A request for one image is not a batch. Routing it here adds a plan, a ledger, and a quote to what should be a single call.
- "Continue the batch" is ambiguous. Check whether it means generating the remaining items or evaluating the ones already produced.
- A completed ledger does not mean the images are good; it means every item produced a verified file. Evaluation is a separate step.
- The delegates are named in full on purpose. Referring to them loosely, as "the run skill", is how a router ends up doing the work itself.

## Never do

- Never perform the batch work in this skill. Route and stop.
- Never install, upgrade, or modify another plugin.
- Never approve a run on the user's behalf, and never run the CLI with
  `--approve` unless the user asked for this batch to be generated.
- Never map an approval to an undisplayed plan or carry it across a changed
  round, prompt, reference set, item set, policy, or remaining call count.
- Never continue past an ambiguous state: route to `image-factory-recover`
  and read the ledger first.

<!-- QUALITY_BASELINE_V1 -->
## When to use（什么时候使用）

当用户需要 **在明确输入、预算和交付约束后执行生成或写入操作** 时加载本技能。先从请求中提取目标、输入、约束、交付格式和验收标准；描述摘要为：Use when the user wants to produce a batch of images, run an image production round, or continue an image batch that already exists. Routes to `image-factory-run` for a batch that has not been generated yet, to `image-factory-judge` for a batch with results to evaluate or a next round to plan, and to `image-factory-recover` for a batch whose state is unclear or that was interrupted. This skill only picks the entry point and never performs the work itself. For a single ad-hoc image with no batch plan, no skill in this plugin applies — ask Codex for the image directly.。

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

校验输入、模型/工具能力、输出路径、预算上限和审批状态；任一关键条件未知时停止在只读阶段。
### Step 3：形成计划

列出将调用的工具、会改变的对象、成功标准以及失败后的安全退出方式。
### Step 4：执行动作

按一次批准执行并记录请求标识；模糊结果先查询而不是重提；每个外部调用均保留可关联的状态或回执。
### Step 5：验证交付

验证产物存在性、格式、哈希/标识、成本状态和质量门禁，并把事实、推断和未验证项分开陈述。

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

付费、发布、覆盖、上传或外部写入必须使用当前任务的显式授权；不自动扩大次数和预算。 如果请求需要别的技能，不复制其正文；按技能名称进行交接，并保留当前任务上下文。

## Progressive disclosure

- 需要确定输入/输出、状态和授权点时，读取 `references/workflow-contract.md`。
- 需要交付前自检时，读取 `references/validation-checklist.md`。
- 遇到超时、部分成功或恢复场景时，读取 `references/error-recovery.md`。
- 首次运行、拒绝越权和失败恢复分别参考 `examples/happy-path.md`、`examples/boundary-refusal.md`、`examples/failure-recovery.md`。
