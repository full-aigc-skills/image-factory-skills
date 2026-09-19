---
name: image-factory-run
description: Use when a batch plan exists and its images have not been produced yet, or when the user asks to generate the images in a plan. Validates the plan, quotes the batch, obtains approval, generates one image per item through Codex, and collects a hash-verified receipt for every artifact. Use when the user says "run this batch" or "generate these". For evaluating results that already exist use `image-factory-judge`; for a run whose state is unclear use `image-factory-recover`.
---

# Run an image batch

## When to use

Use this skill when the user has a batch plan and wants its images produced.
The plan is a JSON document conforming to `schemas/image_batch.schema.json`.

Do not use it to re-run items that already produced a receipt, and do not use it
to decide whether the results are good.

## Workflow

For a goal expressed in conversation, read and follow
[the self-contained conversation workflow](references/conversation-workflow.md).
Keep the visible interaction to direction choices, a compact creation confirmation
card, the exact generation-call count, and the approval request. Keep JSON and CLI
details in the background unless the user asks for them.

When a user describes a batch but has no plan yet, read
[prompt preparation](references/prompt-preparation.md). Use the bundled
template search to prepare prompts and a valid batch plan before validation.
When an approval record already exists, preserve the prompts but do not treat
the record alone as permission to proceed. Verify that it still matches the
exact currently displayed plan, round, and remaining generation-call count.
If it does not, show the current card and require fresh approval. In normal user
copy, say which visible plan detail changed without exposing hashes or ledger
internals.

1Step 1. **Validate the plan before anything else.**

   ```bash
   bin/image-factory validate-plan plan.json --json
   ```

   A non-zero exit means the plan is rejected and nothing will be spent. Fix the
   reported errors and validate again. A plan that asks for a size, a quality
   tier, or a model is rejected on purpose: the built-in image tool accepts only a
   prompt and reference images, so those fields cannot be honoured and are
   refused rather than ignored.

2Step 2. **Quote the batch and show the user the size.**

   ```bash
   bin/image-factory quote plan.json --json
   ```

   Report the image count and make clear that each item costs one generation call
   against the Codex account's image allowance. Quoting itself spends nothing.

3Step 3. **Obtain approval for this exact round.** Show the creation confirmation
   card and quote first. Run only when the user has agreed to generate these
   images. If the plan sets `require_approval_before_run`, the command refuses to
   start without `--approve`. Approval from an earlier round does not apply.
   For a safe `Partial` resume, quote the exact remaining generation-call count
   and obtain fresh approval for those pending items before continuing.
   Bind that approval to the exact plan, round, and remaining generation-call
   count shown on the card. If a prompt, reference image, item, policy, round, or
   count changes, the approval is invalid and a new card and approval are required.

4Step 4. **Run it.**

   ```bash
   bin/image-factory run --plan plan.json --job job.json --destination out/ --approve --json
   ```

   Items already carrying a receipt are skipped, so a resumed run does not
   regenerate finished work.

5Step 5. **Report what happened from the output, not from expectation.** The command
   prints the receipts it collected and the final ledger state. An item is
   `Generated` only when a new image file was found and verified on disk; an exit
   code of zero from Codex without a file is recorded as a failure.

## Inputs

- A batch plan validated against `schemas/image_batch.schema.json`.
- Reference images named by the plan, each no larger than the platform's limit of
  five per item.

## Outputs

- One published image per successful item under `--destination`.
- One receipt per image, conforming to `schemas/artifact_receipt.schema.json`.
- A job ledger conforming to `schemas/factory_job.schema.json`, ending in
  `Completed`, `Partial`, `Failed`, or `Unknown`.

## Platform boundaries

State these to the user rather than working around them:

- Size, quality, background, and image count are fixed by the built-in tool.
  Batch items differ only by prompt and reference images.
- One tool call produces one image, so a fifty-item batch is fifty calls.
- Each call consumes the account's image allowance. A run that hits the limit
  stops there and records the reset time.

## Errors

- `approval_required` — the plan asks for approval and `--approve` was not given.
- `capability_unavailable` — the environment cannot generate; show the probe's
  guidance instead of retrying.
- `quota_exceeded` — the account's image allowance is exhausted. Report the reset
  time and stop.
- `artifact_missing`, `timeout`, `generation_failed` — recorded per item. A
  timeout or success without durable artifact evidence is ambiguous `Unknown`;
  stop later calls and recover without generating. Definite failures are
  recorded as `Failed` and are not silently retried.

## Gotchas

- A zero exit from Codex is not success. Only a new file in the generation directory is, and the command already reports that distinction.
- Two new images appearing for one item means the assignment is ambiguous. The command refuses rather than guessing which one belongs to the item.
- A plan carrying `size` or `quality` will be rejected rather than partially honoured. That is deliberate; move the intent into the prompt instead.
- The same image across two items is flagged for both, because which item owns it cannot be decided from the files.
- A resumed run legitimately reports zero receipts. That means everything was already done, not that the run failed.
- Hitting the usage limit stops the batch. The remaining items stay pending; they are not failed.

## Never do

- Never pass `--approve` without the user's agreement.
- Never bypass approvals or the sandbox. The plugin never passes
  `--dangerously-bypass-approvals-and-sandbox`, and neither should you.
- Never run the batch again to "fix" a failed item. The command never retries a
  failed item, and a silent second attempt is how one bad prompt becomes a large
  bill. Report the failure and let the user decide.
- Never claim a batch succeeded because the command exited zero: read the
  `state` and the receipts.
- Never accept a result the plan did not ask for: if an item produced no new
  file, say so.

<!-- QUALITY_BASELINE_V1 -->
## When to use（什么时候使用）

当用户需要 **在明确输入、预算和交付约束后执行生成或写入操作** 时加载本技能。先从请求中提取目标、输入、约束、交付格式和验收标准；描述摘要为：Use when a batch plan exists and its images have not been produced yet, or when the user asks to generate the images in a plan. Validates the plan, quotes the batch, obtains approval, generates one image per item through Codex, and collects a hash-verified receipt for every artifact. Use when the user says "run this batch" or "generate these". For evaluating results that already exist use `image-factory-judge`; for a run whose state is unclear use `image-factory-recover`.。

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
