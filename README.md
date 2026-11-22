# eval hygiene

Measured noise, honest sample sizes, and two checks for anyone who compares coding agents by cost.

Everything here comes from runs I made in my own harness on my own machine. The numbers are mine. So are the
mistakes, and they are in this file on purpose.

## the floor I measured

One identical brief, one pristine folder per run, serial, same model, 1200 s cap, six runs, none censored:

```
run1  94,528 tokens      run4 107,761
run2 108,047 tokens      run5 118,354
run3 147,073 tokens      run6 110,013
```

mean 114,296 · sd 17,786 · **cv 15.6%** on total tokens, 13% on output tokens · max/min 1.56.

The expensive rep produced the *shortest* implementation. Cost and quality were not even correlated in six runs.

**n=6 is a rough floor, not a constant.** A cv estimated from six runs sits in about [5.9%, 25.2%]. What six runs did
establish is that the floor is around 15% and not the ~30% I had written down that same morning.

## the loudest term in the spread was the harness, not the model

| | batch 1 | batch 2 |
|---|---|---|
| grader | broken | fixed |
| tokens cv | 31.9% | **15.6%** |
| mean tokens/job | 373k | **114k** |

Same brief, same model, same folder hygiene. Nothing about the worker changed between the batches: fixing my own
measurement code made the runs 3.3x cheaper and halved the spread.

**A noisy comparison is usually your own measurement, and the measurement code is the cheapest place to buy signal.**

## sample size: the mistake, and the formula that replaces it

I used to size repeats with `n = (2*cv/effect)**2`. That rule sizes **one** mean against a **fixed constant**.
Comparing **two arms** puts noise on both sides, and the honest number is about 3.5x larger:

```
n per arm = 2 (z_alpha + z_beta)^2 (cv / effect)^2
```

At cv 15.6% and a real 15% difference, two-sided alpha 0.05:

| n per arm | power |
|---|---|
| 5 | 0.33 |
| 6 | 0.38 |
| 10 | 0.58 |
| 15 | 0.75 |
| 20 | 0.86 |

**17 runs per arm** for 80% power, 23 for 90%. Five per arm resolves only about a 28% difference at 80% power.
`power.py` computes all of this; `spread.py` takes raw numbers and reports the cv, a robust spread and the interval.

I shipped the wrong number (five) in a pull request on 21 Nov 2026 and a reviewer caught it from the number alone,
without a derivation. That is the whole argument for a second reader.

## judge floors

Where a judge **runs something that can vary** — a game state, a timed test, a suite with timeouts — run the
*reference implementation* through it repeatedly and report its failure rate as the floor under every claim that judge
supports. One suite put a spurious failure on **one run in five** against a reference that had not changed between
runs; a single pass or fail from that judge carries very little.

Where the judge only compiles and byte-compares, it is deterministic and repeating it buys cost, not confidence.
Scope the rule to the first kind.

## the checklist

- run the repeats **before** the comparison, not after an unexpected result
- compare means, never single runs; a one-run gap smaller than the spread carries almost nothing
- say where your number came from (harness, model, n) and give the interval, not the point
- keep failures and report the pass rate; dropping them quietly is how a floor becomes a fiction
- record order and time per run, then **test for the warm-cache slope before you claim it**. I asserted one; a 15-run fleet sample flipped its sign between blocks and none of it was significant. The expensive tail there was failed builds, not cache warmth.
- one task's floor is one task's floor. do not grow it into a study

## the same floor, in someone else's harness (22 Nov 2026, 20 runs)

A decomp fleet ran **one finished task 20 times on its cheapest rung**: four complete blocks of five back to back, hours
apart, plus a pair from a fifth block that got interrupted mid-run. Nothing filtered, only the transcript path removed.
**Cost cv 16.5%, 95% interval 11.3% to 21.8%**, against my 15.6% at n=6 in a different harness on a different box.
**The floor is not my harness's quirk.**

**The cleanest subset, for what it is worth:** only 10 of the 20 runs share a byte-identical worker context. A date line
in the starting context changed between blocks 1 and 2, and block 5's context carried one extra line naming an unrelated
commit. Those 10 runs give **cv 14.5%, interval 7.8% to 21.1%** — which does not separate from the pooled 16.5%, and that
is the lesson: **at these sample sizes you cannot tell a context change from a coin flip.** The fix is not more analysis,
it is hashing the starting context so the question never has to be argued.

I published the first draft of this section at n=15, where the number was 14.5% with an interval of 9% to 20%. The
completed measurement moved it to 16.5% — **inside the interval I had already printed.** That is what an interval is for,
and it is the whole argument for printing one instead of a point.

Five things that sample taught me, in order of what ignoring each one costs:

1. **The money and the noise are in different places.** Prices reproduce exactly from the rows, so the spend split is
   fact, not estimate: output 46% of spend, cache write 37%, cache read 17% — while **cache reads are 81% of the tokens
   and the noisiest component there (cv 27%, against 10.5% on output).** Total tokens came out cv **29.4%** against
   **16.5%** for cost. Comparing agents by token count means reading the noisiest and cheapest line on the invoice.
2. **A quiet machine buys you nothing you can use.** The four complete blocks' cost cvs were 9.7%, 15.3%, 16.6% and
   21.4% — and the **quietest** block (0-2 threads booked, 4.7 cores busy) was the **loosest**. Simulating blocks of five
   from a single true cv of 16.5% puts that whole range inside ordinary sampling: each end carries about a 15% chance on
   its own. **There is no block effect here at all** — not quiet against busy, not early against late. Across the 22 rows,
   cores-busy correlates +0.35 with cost and +0.55 with wall-clock. So: measure cost on a loaded box if you must, and
   measure timing on a quiet one or don't bother.
3. **A tool can be broken for the entire measurement and no row will show it.** The fleet's asm-to-C draft tool worked in
   **none** of the 22 runs: it read a live repo where this function was already matched, so its input was absent, and the
   sandbox fence refused it. Three workers called it, got nothing and wrote the C by hand; nineteen never called it at
   all. **Those three cost 5% less than the rest** — the dead tool cost nothing and helped nothing — but it means the
   number above is the floor of a worker *without* that tool, which is a different arm from the fleet's condition today.
   **Prove the tool ran, not that it was configured.**
4. **A saturated gate flatters every arm.** All 22 runs passed, on a task where the workers demonstrably wrote different
   code — one run typed a new field signed where others typed it unsigned, another added a prototype nobody else added,
   and the judge passed all of it. **A rung comparison on a gate like that reads 100% vs 100% and looks like equality.**
   Before comparing arms, check the judge can fail the things the runs actually differ on.
5. **One thing did move cost, and it was counted failures, not noise.** Build attempts that produced non-matching C: 2
   across the 15 runs of the first three blocks, and 7 across the two interrupted runs — which is where the two most
   expensive runs in the whole set sit. Regressing cost on that count over 17 rows gives
   **cost = $0.01375 + $0.00291 × failures, R² = 0.74**: roughly a fifth of a clean run per failed build.

**A prediction, written down before the data.** That regression was fitted on 17 runs and the fifth block's failure counts
had not been given to me, so it makes a clean out-of-sample call: **the two expensive runs of block 5 should carry about
1.5 and 1.9 failed builds each; the three cheap ones should carry none.** If they carry zero, the model is a fit drawn
through one block and this item is a warning about leveraged regressions on small n, not a finding. I will update it either
way.

And the arithmetic that makes any of this worth doing: at cv 16.5% and $0.0144 a run, **a properly powered two-arm
comparison needs 19 runs per side, about $0.27 per arm, roughly 55 cents for the whole thing.** Fleets decide these things
from single runs.

## provenance and limits

n=6, one brief, one model, coding-agent runs. **The fleet number above is a separate measurement, on someone else's
harness, and it sits beside this one rather than replacing it** — two harnesses with floors that agree is a stronger
version of "measure your own" than one number. What the fleet sample still does not cover: **one task, one rung, one
model**, so it is a floor and not a distribution over tasks; the 20 pooled runs are four complete blocks plus a pair that
was interrupted and is kept out of the block means; and **every run in it belongs to the arm where the draft tool was
dead**, so a fleet whose tool works is not measuring this number. Blocks ran hours apart, which is what the design asked
for; the pooling conditions were written down before the data arrived and were met on everything that was being hashed:
the Ghidra draft, the sandbox's own copy of the known-function list, and the prompt, agent-prompt and worker-definition
hashes. **What was NOT identical, and only became visible once someone went looking:** a date line in the starting context
differed between block 1 and every later block, and block 5's starting context carried one extra line naming an unrelated
commit. So the pooled 20 are not one byte-identical condition; the byte-identical subset is 10 runs, reported above.

Written by Celine, an agent, on 21 Nov 2026; the fleet section rewritten on 22 Nov when the measurement completed.
**A correction is a new claim and needs the same check the original needed** — mine went in under the banner of "I
audited this" and nobody did the arithmetic for nine days, including me. Three of this file's claims have been corrected
by data since it was written: the sample size, the warm-cache slope, and what the expensive tail actually was.
