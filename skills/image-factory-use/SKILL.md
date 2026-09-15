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
