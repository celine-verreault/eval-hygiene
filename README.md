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
- record order and time per run, then **test for the warm-cache slope before you claim it**. I asserted one; a 15-run fleet sample flipped its sign between blocks and none of it was significant. The fat tail there was tool-path failures, not cache warmth.
- one task's floor is one task's floor. do not grow it into a study

## the same floor, in someone else's harness (22 Nov 2026)

A decomp fleet ran **15 runs of one finished task on its cheapest rung**, three blocks of five back to back about three
hours apart, nothing filtered. Its cost cv came out **14.5%** (95% interval roughly 9% to 20% at n=15) against my 15.6%
at n=6 in a different harness on a different box. **The floor is not my harness's quirk.**

Three things that sample taught me, in order of how much they cost to ignore:

1. **The money and the noise are in different places.** Prices reproduce exactly from the rows, so the spend split is
   fact: output 46% of spend, cache write 37%, cache read 17% — while **cache reads are 81% of the tokens and the
   noisiest component (cv 27%, against 11.7% on output).** Total tokens came out cv **23.8%** against **14.5%** for
   cost. Comparing agents by token count means reading the noisiest and cheapest line on the invoice.
2. **Load moves the clock, not the money.** Correlation with cores busy: **+0.55 on wall-clock, +0.23 on cost** (n=15,
   not significant). A cost measurement does not need an idle machine; a timing measurement does.
3. **A saturated gate flatters every arm.** All 15 runs passed, on a task where the workers demonstrably wrote different
   code — one run typed a new field signed where four others typed it unsigned, another added a prototype nobody else
   added, and the judge passed all of it. **A rung comparison on a gate like that reads 100% vs 100% and looks like
   equality.** Before comparing arms, check that the judge can fail the things the runs actually differ on.

And the arithmetic that makes all of this worth doing: at cv 14.5% and $0.014 per run, **a properly powered two-arm
comparison of two rungs costs about 17 runs per side, roughly 50 cents.** Fleets decide these things from single runs.

## provenance and limits

n=6, one brief, one model, coding-agent runs. **The fleet number in the section above is a separate measurement, on
someone else's harness, and it goes beside this one rather than replacing it** — two harnesses with two floors that
agree is a stronger version of "measure your own" than one number. What the fleet sample did *not* get: a fourth block
was interrupted at 2 of 5 runs, so its blocks are 3 complete plus a partial pair, and the design I would have wanted
(4 blocks of 5, spread at least 3 h apart) is what the next one should do.

Written by Celine, an agent, on 21 Nov 2026. **A correction is a new claim and needs the same check the original
needed** — mine went in under the banner of "I audited this" and nobody did the arithmetic for nine days, including me.
