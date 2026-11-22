#!/usr/bin/env python3
"""Sample size and power for comparing two agent arms by cost.

The mistake this exists to prevent: `n = (2*cv/effect)**2` sizes ONE mean against
a fixed constant. Comparing two arms puts noise on both sides, and the real
number is about 3.5x larger. I made that mistake, shipped it in a pull request,
and a reviewer caught it from the number alone.

Stdlib only. Run with no arguments for the worked example.
"""
from math import sqrt, erf

Z = {0.80: 0.8416, 0.90: 1.2816, 0.95: 1.6449}   # one-sided z for the wanted power
Z_ALPHA = 1.959964                                # two-sided alpha = 0.05


def phi(z):
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def power(cv, effect, n_per_arm, z_alpha=Z_ALPHA):
    """Probability of calling a real `effect` (as a fraction of the mean) significant,
    comparing two arms of `n_per_arm` runs each with coefficient of variation `cv`."""
    return phi(effect / (cv * sqrt(2.0 / n_per_arm)) - z_alpha)


def n_per_arm(cv, effect, wanted_power=0.80, z_alpha=Z_ALPHA):
    """Runs per arm needed to reach `wanted_power` on a real `effect`."""
    return 2.0 * (z_alpha + Z[wanted_power]) ** 2 * (cv / effect) ** 2


def smallest_detectable(cv, n_per_arm, wanted_power=0.80, z_alpha=Z_ALPHA):
    """The smallest real difference `n_per_arm` per arm can resolve at `wanted_power`."""
    return (z_alpha + Z[wanted_power]) * cv * sqrt(2.0 / n_per_arm)


def cv_interval(cv, n):
    """Rough interval for the cv ITSELF estimated from n runs: SE(cv) ~ cv/sqrt(2(n-1)).
    Assumes normality, which cost is not, so treat this as optimistic."""
    if n < 3:
        return (float("nan"), float("nan"))
    rel = 1.0 / sqrt(2.0 * (n - 1))
    return (cv * (1.0 - 1.96 * rel), cv * (1.0 + 1.96 * rel))


if __name__ == "__main__":
    cv, effect = 0.156, 0.15
    print(f"cv = {cv:.1%}, real difference = {effect:.0%}, two-sided alpha = 0.05\n")
    print(" n per arm   power")
    for n in (5, 6, 10, 15, 17, 20):
        print(f"      {n:>3}     {power(cv, effect, n):.2f}")
    print(f"\nruns per arm for 80% power:  {n_per_arm(cv, effect):.1f}")
    print(f"runs per arm for 90% power:  {n_per_arm(cv, effect, 0.90):.1f}")
    print(f"what 5 per arm can resolve at 80% power: {smallest_detectable(cv, 5):.1%}")
    lo, hi = cv_interval(cv, 20)
    print(f"a cv estimated from 20 runs sits in [{lo:.1%}, {hi:.1%}] (1-sigma normal approx)")
