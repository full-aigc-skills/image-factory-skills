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
[the shared conversation workflow](../image-factory-use/references/conversation-workflow.md).
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
