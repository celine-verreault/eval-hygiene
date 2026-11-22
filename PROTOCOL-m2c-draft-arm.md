# Protocol: does an asm-to-C draft tool change worker cost, and is it worth measuring?

Written by Celine, an agent, on 22 Nov 2026, for a decomp fleet that runs worker agents on one function at a time.
Task-specific identifiers are left out on purpose; the numbers come from 22 measured runs of one finished task on the
fleet's cheapest rung.

## 0. The arithmetic that decides whether to run anything at all

Measured on the 22 runs, no draft tool working:

| quantity | value |
|---|---|
| mean cost per run | $0.0144 |
| cost noise floor (cv) | 16.5%, 95% interval 11.3% to 21.8% |
| price of one failed build | +$0.00323 (about 21% of a clean run) |
| failed builds per run | 4 in 20 = 0.20 |

**A draft tool's only cost path is removing retries.** If it removed *every* failed build, mean cost would fall by
0.20 x $0.00323 = **$0.00065, which is 4.5% of a run.** That is the ceiling on the benefit, so:

| to detect | n per arm |
|---|---|
| a 15% cost change | 19 |
| a 10% cost change | 43 |
| **the 4.5% that is the maximum possible effect** | **221** |

**Therefore: do not measure cost directly.** The effect is three times smaller than what a cheap arm can resolve.
Measure the *rate* and derive the money through the price above.

| to detect | n per arm |
|---|---|
| failed builds 20% -> 0% | **32** |
| failed builds 20% -> 10% | 197 (not worth it) |

Recorded caveat: the 0.20 baseline is 4 events in 20 runs, so its own 95% interval is about 0.06 to 0.46. If the true
rate sits at the low end, 32 per arm is underpowered even for the rate.

## 1. Stage 0 - measure the tool, not the loop (no worker runs, essentially free)

The causal claim is "the draft is good". That is testable without a single agent run.

1. For a set of sandboxes, call the tool with the **worker's own sandbox path** and record per case: does the draft
   build, does it match the accepted C byte for byte, and how far off is it otherwise.
2. **Control: call it the bare relative way on the same input and diff the two drafts.** A bare path that resolves
   against the live checkout reads headers that already contain the solved type, so its draft can carry the answer.
   This control demonstrates the leak or rules it out for the price of two calls.
3. Run the judge on the base with no worker and no tokens: a control row, and the oracle that is not the author.
4. **Re-verdict every stored draft under the new judge key.** If the gate's rules moved (for example, noted cast
   exceptions), a previous "the gate passed everything" finding has to be re-checked or rewritten.

**Hazard in the leak demo itself: the bare-path call writes into the live checkout.** Hash the live checkout before and
after the demo, revert what it wrote, and confirm the solved header is untouched. A demonstration of a contamination bug
should not contaminate.

## 2. Go / no-go, written before the Stage 0 data exists

**Stage 1 runs only if the sandbox-path draft builds in at least 70% of cases and matches outright in at least 30%.**
Below that the tool is a hint rather than a draft, the retry rate is unlikely to move, and the 32+32 is money spent to
confirm what the drafts already showed. No-go is a result, not a failure.

## 3. Stage 1 - the arm

- **Question:** does a working draft tool reduce failed builds per run?
- **Primary outcome:** failed builds per run. Cost is reported as a derived quantity: rate change x $0.00323.
- **Design:** 32 per arm, randomised, **both arms interleaved in one launching session**, so the session is a block that
  cancels instead of a treatment. Launching session changes harness version, request shape, session context and git
  snapshot; all of them are recorded per row.
- **The treatment is an instruction, not availability.** In 22 runs, 3 workers called the tool unprompted. An
  availability-only arm measures uptake, not the tool. So: two prompt variants differing only in the line that names the
  tool and its call form, **both prompt hashes recorded**. Changing the prompt makes this a new arm; write that down
  before the run, not after.
- **Do not compare new rows against the 22 baseline rows as if they were a control.** Tool, judge, fence and prompt all
  differ. The 22 are the noise floor of the old condition, nothing more.

### Gates before run 1. Each of these has already caused a bad measurement once.

1. The tool reads **only** the tree its argument names, with no fallback to the live checkout and no directory-name
   substitution. Anything else is refused. A tool that can read the answer makes the treatment arm contaminated by
   whichever worker happens to type a relative path, and the verdict will not show it.
2. The live checkout is hashed before and after each block, including a write check on its draft output directory.
3. The new judge's control row lands first.
4. Every row carries its context hashes and their provenance.

### Fields every row must carry

`failed_builds` (test failures, excluding the first expected include-file failure, counted once per call after
de-duplicating the transcript), tool calls made, tool calls that returned output, and the call form used. **A hash of a
tool is not a check that the tool works: the tool was dead for all 22 measured runs and every hash would have looked
correct.**

## 4. The measurement that beats this experiment

One task's 0.2 failure rate is too thin to power anything cheap. **Put `failed_builds` and the tool-call fields into
every row the fleet writes, and the question answers itself across a week of real work on every task, with no study at
all.** The row already passes through; the measurement belongs in it.

## 5. What each result would mean

- Rate drops, drafts were good: the tool works, and the money follows from the price measured here.
- Rate flat, drafts were good: draft quality is not the binding constraint. Look at what the workers actually failed on
  (store order, type reasoning) rather than at the tool.
- Rate flat, drafts were bad: Stage 0 already said so, and Stage 1 should not have run.

## 6. Superseded on the day it was written (22 Nov, 18:2x)

The fleet's judge now writes, into **every** row: `test_runs`, `failed_test_runs`, `failed_test_runs_before_edit`, and
per allowed tool entry `tool_calls` with `calls`, `refused` and `with_output`. Checked against the 22 runs above, it
reproduces the hand counts exactly.

**Consequence: Stage 1 is parked, not run.** The primary outcome of this design is now a standing field, collected on
every task and every model instead of one task on the cheapest rung, at no extra cost. Spending 32 + 32 runs to measure
what the fleet reports for free would be paying for a worse copy of the same number.

`failed_test_runs_before_edit` is better than the design above, and specifically fixes its worst part: the original
needed a task-specific definition of "the first failure that does not count", which would not have travelled between
tasks. Subtracting the before-edit failures removes that definition entirely.

What the standing fields still cannot answer, and the only residue worth an arm later: **the counterfactual of a worker
that was told about the tool versus one that was not.** Uptake is visible in the rows (`calls`, `refused`, `with_output`);
the effect of the prompt line is not. Hold it until the rows show low uptake — if real rounds already call the tool the
question is moot, and if they never call it, the prompt line earns its small arm then, on evidence.

When a week of rows exists, the analysis is observational and must not compare raw rates across tasks: stratify by task
and model, or regress with the launching session as the cluster, as in the noise-floor note.

**Open definition, asked and unanswered:** does "edit" mean any write inside the sandbox, or only the draft C file? A
worker that edits a header and re-runs must not have that failure counted as before-edit, or the subtraction hides a real
failure of the worker's own code.
