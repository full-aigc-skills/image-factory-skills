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
[the shared conversation workflow](../image-factory-use/references/conversation-workflow.md)
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
