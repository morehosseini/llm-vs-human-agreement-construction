#!/usr/bin/env python3
"""
Supplementary reproducibility script.
Calculates human reliability (Fleiss' and Cohen's kappa) and confidence-ranked coverage accuracy.

Run:  python scripts/human_reliability_and_coverage.py
Outputs: data/human_reliability_and_coverage.json
"""
import json
import os
import numpy as np
import pandas as pd

# Define paths relative to the script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")

W = pd.read_csv(os.path.join(DATA_DIR, "unified_labels.csv"))

S, R, M = W["H_S"], W["H_R"], W["H_M"]
MODELS = ["GPT-5 Full", "GPT-5 mini", "Gemini 2.5 Flash", "Gemini Pro"]

def cohen_kappa(a, b):
    m = a.notna() & b.notna()
    aa, bb = a[m].astype(str), b[m].astype(str)
    cats = sorted(set(aa) | set(bb))
    idx = {c: i for i, c in enumerate(cats)}
    n = len(aa)
    k = len(cats)
    O = np.zeros((k, k))
    for x, y in zip(aa, bb):
        O[idx[x], idx[y]] += 1
    po = np.trace(O) / n
    pe = ((O.sum(1) / n) * (O.sum(0) / n)).sum()
    return int(m.sum()), round(float(po), 3), round(float((po - pe) / (1 - pe)), 3)

def fleiss_kappa(df):
    cats = sorted(set(df.values.ravel().astype(str)))
    ci = {c: i for i, c in enumerate(cats)}
    N, n = len(df), df.shape[1]
    counts = np.zeros((N, len(cats)))
    for i, (_, row) in enumerate(df.iterrows()):
        for v in row:
            counts[i, ci[str(v)]] += 1
    pj = counts.sum(0) / (N * n)
    Pi = ((counts ** 2).sum(1) - n) / (n * (n - 1))
    return round(float((Pi.mean() - (pj ** 2).sum()) / (1 - (pj ** 2).sum())), 3)

triple = S.notna() & R.notna() & M.notna()
out = {
    "triple_labelled_n": int(triple.sum()),
    "fleiss_kappa_triple": fleiss_kappa(W.loc[triple, ["H_S", "H_R", "H_M"]]),
    "pairwise_human_cohen_kappa": {},
    "precision_at_coverage_highconf": {},
}
for a, b, nm in [(S, R, "S-R"), (S, M, "S-M"), (R, M, "R-M")]:
    n, po, k = cohen_kappa(a, b)
    out["pairwise_human_cohen_kappa"][nm] = {"common_records": n, "agreement": po, "cohen_kappa": k}

# Precision@coverage on HighConf (Majority 3-0 / 2-1), confidence-ranked
hc = W[W.tier.isin(["Majority 3-0", "Majority 2-1"])]
COV = [0.10, 0.25, 0.50, 0.75, 1.00]
for m in MODELS:
    d = hc[["benchmark", f"AI_{m}", f"CONF_{m}"]].dropna().sort_values(f"CONF_{m}", ascending=False)
    correct = (d["benchmark"].astype(str) == d[f"AI_{m}"].astype(str)).values
    n = len(d)
    out["precision_at_coverage_highconf"][m] = {
        f"top_{int(c*100)}pct": round(float(correct[:max(1, int(round(c * n)))].mean()), 3) for c in COV
    }
    out["precision_at_coverage_highconf"][m]["n"] = int(n)

output_path = os.path.join(DATA_DIR, "human_reliability_and_coverage.json")
with open(output_path, "w") as f:
    json.dump(out, f, indent=2)
print(f"Saved human reliability and coverage metrics -> data/human_reliability_and_coverage.json")
