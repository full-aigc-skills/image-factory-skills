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
[the shared conversation workflow](../image-factory-use/references/conversation-workflow.md)
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
