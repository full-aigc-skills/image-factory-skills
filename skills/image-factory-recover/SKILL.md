---
name: image-factory-recover
description: Use when an image batch was interrupted, when a ledger reports a state the user does not understand, or when the user asks what happened to a batch and whether it is safe to continue. Reads the job ledger, maps the current state to the single legal next step, and reports it without spending anything. Use when the state is `Running`, `Unknown`, or `Partial`, or when a previous attempt stopped unexpectedly. For a batch that has not been started use `image-factory-run`.
---

# Recover an image batch

## When to use

Use this skill whenever a batch's condition is uncertain: a run that was
interrupted, a command that timed out, a state the user does not recognise, or a
question about what already exists.

Do not use it to generate anything, and do not use it to evaluate results.

## Workflow

Read and follow
[the self-contained conversation workflow](references/conversation-workflow.md)
for the user-facing recovery message. Summarize the state, completed/failed/pending
counts, remaining generation-call count, and one legal next action in plain language.

1Step 1. **Read the ledger before doing anything else.**

   ```bash
   bin/image-factory status --job job.json --json
   ```

   The ledger is the record of what was actually attempted, so read it rather
   than inferring the situation from files on disk.

2Step 2. **Validate the plan that is still on disk**, so you know what the batch was
   supposed to do:

   ```bash
   bin/image-factory validate-plan plan.json --json
   ```

3Step 3. **Reconcile only a command-supported recoverable state.** Call
   `recover` only when `status` reports `Running`, `Unknown`, `Partial`, or `Completed`.
   For every other state, do not call `recover`; use the legal non-reconcile
   action in the table below.

   The command validates
   every per-item receipt against the artifact on disk, marks stale attempts
   without a matching receipt `Unknown`, and rebuilds the receipt manifest. It
   makes zero generation calls. Recovery is evidence reconciliation, never a
   diagnostic generation attempt.

   ```bash
   bin/image-factory recover --plan plan.json --job job.json --destination out/ --json
   ```

4Step 4. **Map the reconciled state to the single legal next step.** Do not
   improvise beyond it.

   | State | Meaning | Next step |
   | --- | --- | --- |
   | `Draft` | The job exists and nothing was validated | Validate the plan, then run |
   | `PlanValidated` | The plan passed validation and was not approved | Obtain approval, then run |
   | `Approved` | Approved and not yet started | Run |
   | `Running` | A run was in progress and did not finish | Reconcile receipts; unresolved attempts become `Unknown` |
   | `Evaluated` | A verdict was reached | Judge the outcome or optimize the failing items |
   | `PendingApproval` | Deterministic evaluation passed but required human labels are missing | Return to judge and ask only for the missing labels |
   | `Optimized` | A next round exists | Validate the next plan, quote the exact remaining generation calls, obtain fresh approval, then run and evaluate |
   | `Accepted` | Every required result was explicitly accepted | Terminal; do not run, recover, or optimize |
   | `Completed` | Every item produced a verified artifact | Evaluate the batch |
   | `Partial` | The run finished without completing every item | If pending items remain, quote them and seek fresh approval; with no pending items and only definite failures, evaluate them and then request an explicit rewrite or retry-unchanged; if any item is unknown, reconcile and stop if unresolved |
   | `Failed` | The job cannot proceed and is terminal | Report why, and start a new job if the user wants to try again |
   | `Unknown` | An interruption left the outcome unresolved | Query the state; do not re-run to find out |

5Step 5. **Report the completed, failed, pending, and unknown counts**, then give
   exactly one legal next action. If any item is `Unknown`, explain that its
   external outcome is ambiguous and stop; never suggest a retry as a diagnostic
   action.

   If the recovery report still contains `Unknown`, say that the external call
   may have happened and its outcome cannot be proved. Do not re-run it to find
   out, and do not offer a new generation while the ambiguity remains.

   When `Partial` has no pending or unknown item, `Failed` and `Skipped` are
   definite failures rather than ambiguous calls. Evaluate them as
   `missing_artifact`; after the job becomes `Evaluated`, ask for an explicit
   rewrite or explicit retry-unchanged decision. Do not run them automatically.

6Step 6. **Report the failure categories and the usage limit if one is present.** A
   ledger carrying `quota_exceeded` holds the reset time for the image
   allowance. Report it and wait.

7Step 7. **Tell the user what continuing would cost** before resuming: how many items
   are still pending, and therefore how many generation calls the resume would
   make. Only the items with no recorded attempt are pending.

## Platform boundaries

Recovery cannot change what a generation call produces. Size, quality,
background, and image count are fixed by the built-in tool, so resuming an item
reproduces the same kind of output as before. If the user wants a different
result, that is a new round with a rewritten prompt, not a recovery.

## Inputs

- A job ledger conforming to `schemas/factory_job.schema.json`.

## Outputs

- A report of the state, the per-item states and failure categories, any usage
  limit with its reset time, and the single legal next step.

## Errors

- A missing or unreadable ledger is reported as an error rather than treated as
  an empty job. A ledger that cannot be read is a fact to surface, not a blank
  slate to overwrite.
- A ledger holding anything resembling a credential is refused on read. Report
  that as a problem with the file rather than working around it.

## Gotchas

- An unreadable ledger is not an empty one. Overwriting it discards the only record of what was already spent.
- `Running` does not mean the batch is progressing; it means a run did not finish. Reconcile it before naming a next action.
- `Partial` is a normal outcome, not corruption. Items that failed are not pending, so a resume will not touch them.
- A usage limit is not a failure of the batch. Report the reset time instead of resuming.
- Finished items are skipped on resume by design. Reporting "nothing happened" when the ledger shows zero pending items is misleading.
- Never resume a ledger whose state is `Failed`. It is terminal so that a bad prompt cannot become a repeated charge.

## Never do

- Never re-run a batch to discover its state. Read the ledger first; a re-run is
  how an interrupted batch becomes a double charge.
- Never treat an unreadable ledger as an empty one, and never overwrite it to
  continue.
- Never resume past `Failed`: it is terminal on purpose, and continuing requires
  a new job.
- Never retry an item that has a recorded attempt. Only items with no attempt
  are pending.
- Never continue while a usage limit is in force; report the reset time instead.

<!-- QUALITY_BASELINE_V1 -->
## When to use（什么时候使用）

当用户需要 **从已记录状态恢复中断任务，避免重复提交或重复计费** 时加载本技能。先从请求中提取目标、输入、约束、交付格式和验收标准；描述摘要为：Use when an image batch was interrupted, when a ledger reports a state the user does not understand, or when the user asks what happened to a batch and whether it is safe to continue. Reads the job ledger, maps the current state to the single legal next step, and reports it without spending anything. Use when the state is `Running`, `Unknown`, or `Partial`, or when a previous attempt stopped unexpectedly. For a batch that has not been started use `image-factory-run`.。

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

核对任务标识、最后成功阶段、远端状态、预算和授权范围；任一关键条件未知时停止在只读阶段。
### Step 3：形成计划

列出将调用的工具、会改变的对象、成功标准以及失败后的安全退出方式。
### Step 4：执行动作

仅继续尚未完成且可证明安全的阶段；每个外部调用均保留可关联的状态或回执。
### Step 5：验证交付

返回复用结果、新执行步骤、未恢复项和下一人工决策点，并把事实、推断和未验证项分开陈述。

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

没有幂等键、远端状态或用户授权时不重提任务；恢复不扩大原批准范围。 如果请求需要别的技能，不复制其正文；按技能名称进行交接，并保留当前任务上下文。

## Progressive disclosure

- 需要确定输入/输出、状态和授权点时，读取 `references/workflow-contract.md`。
- 需要交付前自检时，读取 `references/validation-checklist.md`。
- 遇到超时、部分成功或恢复场景时，读取 `references/error-recovery.md`。
- 首次运行、拒绝越权和失败恢复分别参考 `examples/happy-path.md`、`examples/boundary-refusal.md`、`examples/failure-recovery.md`。
