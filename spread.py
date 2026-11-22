#!/usr/bin/env python3
"""Spread of repeated cost measurements, the honest way: cv AND a robust spread.

Cost per run is right-skewed, so a few fat-tailed runs inflate the cv. Report both
the cv and IQR/median, and report the interval on the cv rather than the point.

    python3 spread.py 114000 94528 108047 ...
    cat runs.txt | python3 spread.py
"""
import sys
from statistics import mean, median, stdev, quantiles
from power import cv_interval


def report(xs, name="runs"):
    n = len(xs)
    if n < 3:
        print(f"{name}: n={n} is too few to spread. measure more or say n.")
        return
    m, sd = mean(xs), stdev(xs)
    cv = sd / m
    q = quantiles(xs, n=4, method="inclusive")
    iqr = q[2] - q[0]
    lo, hi = cv_interval(cv, n)
    print(f"{name}: n={n}")
    print(f"  mean {m:,.0f}   sd {sd:,.0f}   cv {cv:.1%}")
    print(f"  median {median(xs):,.0f}   IQR {iqr:,.0f}   IQR/median {iqr/median(xs):.1%}")
    print(f"  min {min(xs):,.0f}   max {max(xs):,.0f}   max/min {max(xs)/min(xs):.2f}")
    print(f"  cv interval (normal approx, optimistic for skewed cost): [{lo:.1%}, {hi:.1%}]")
    print(f"  -> a comparison on this arm needs ~{2*(1.959964+0.8416)**2*(cv/0.15)**2:.0f} runs per side"
          f" to resolve a 15% difference at 80% power")


if __name__ == "__main__":
    raw = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()
    xs = [float(t.replace(",", "")) for t in raw.replace("\n", " ").split() if any(c.isdigit() for c in t)]
    report(xs)
