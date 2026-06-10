#!/usr/bin/env python3
"""
Replication pipeline for the main analysis.
Calculates agreement metrics, builds the unified dataset, and outputs results.

Run:  python scripts/analysis.py
Outputs: data/results.json, data/unified_labels.csv, figures/figure13_calibration.png, figures/figure14_dendrogram.png
"""
import json
import os
import warnings
import hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform

warnings.filterwarnings("ignore")

# Define paths relative to the repository root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
FIGS_DIR = os.path.join(ROOT_DIR, "figures")
os.makedirs(FIGS_DIR, exist_ok=True)

RNG = np.random.default_rng(20260529)

SIXCLASS = [
    "Not Related",
    "Uncertain",
    "AI Development and Methods",
    "AI Adoption Factors",
    "AI Performance Evaluation",
    "AI Economic and Business Impacts"
]

def norm_label(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return None
    # Canonical map for minor spelling variants
    m = {
        "ai development & methods": "AI Development and Methods",
        "ai econ. & business impacts": "AI Economic and Business Impacts",
        "ai economic and business impact": "AI Economic and Business Impacts",
    }
    return m.get(s.lower(), s)

# ---------------------------------------------------------------- load AI CSVs
AI_FILES = {
    "GPT-5 Full":       os.path.join(DATA_DIR, "result_GPT5_Full.csv"),
    "GPT-5 mini":       os.path.join(DATA_DIR, "result_gpt_5_mini.csv"),
    "Gemini Pro":       os.path.join(DATA_DIR, "result_Geminipro.csv"),
    "Gemini 2.5 Flash": os.path.join(DATA_DIR, "result_gemini_2.5_flash.csv"),
}
ai = {}
for name, path in AI_FILES.items():
    df = pd.read_csv(path)
    # Standardise: positional index 0..1803
    if "Unnamed: 0" in df.columns:
        df = df.rename(columns={"Unnamed: 0": "row"})
    else:
        df["row"] = np.arange(len(df))
    df["row"] = df["row"].astype(int)
    df = df[["row", "DOI", "Abstract", "AI_Category", "AI_Confidence", "AI_Reason"]].copy()
    df["AI_Category"] = df["AI_Category"].map(norm_label)
    ai[name] = df.set_index("row")
    print(f"AI {name:18s}: {len(df)} rows, conf[{df.AI_Confidence.min():.2f},{df.AI_Confidence.max():.2f}]")

# ---------------------------------------------------------------- load humans (anonymised)
HUM_FILES = {
    "S": os.path.join(DATA_DIR, "human_labels_s.csv"),
    "R": os.path.join(DATA_DIR, "human_labels_r.csv"),
    "M": os.path.join(DATA_DIR, "human_labels_m.csv"),
}
hum = {}
reason_R = None
for code, path in HUM_FILES.items():
    df = pd.read_csv(path)
    df["label"] = df["label"].map(norm_label)
    hum[code] = df.set_index("row")
    if code == "R":
        reason_R = df.set_index("row")["reason"].map(
            lambda x: None if (x is None or (isinstance(x, float) and np.isnan(x)) or str(x).strip() == "") else str(x).strip()
        )
    print(f"HUM {code}: {len(df)} rows, labelled={df.label.notna().sum()}")

# ---------------------------------------------------------------- alignment check
def ab_sig(s):
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    return hashlib.md5(str(s).strip()[:80].lower().encode()).hexdigest()[:8]

N = 1804
base_ab = ai["GPT-5 Full"]["Abstract"]
match_rates = {}
for code in hum:
    common_idx = hum[code].index
    a = base_ab.loc[common_idx].map(ab_sig).values
    b = hum[code]["Abstract"].map(ab_sig).values
    match_rates[code] = float(np.mean(a == b))
print("Abstract alignment (AI row vs human row):", match_rates)

# ---------------------------------------------------------------- build wide table
W = pd.DataFrame(index=range(N))
W["DOI"] = ai["GPT-5 Full"]["DOI"]
for code in hum:
    W[f"H_{code}"] = hum[code]["label"]
for name in ai:
    W[f"AI_{name}"]      = ai[name]["AI_Category"]
    W[f"CONF_{name}"]    = ai[name]["AI_Confidence"]
    W[f"REASON_{name}"]  = ai[name]["AI_Reason"]
W["reason_excl_R"] = reason_R

# ---- human majority vote + agreement tier
def majority(row):
    labs = [row[f"H_{c}"] for c in ["S", "R", "M"]]
    labs = [l for l in labs if pd.notna(l)]
    k = len(labs)
    if k == 0:
        return (None, "No label", 0, 0)
    from collections import Counter
    ct = Counter(labs)
    top, topn = ct.most_common(1)[0]
    if k == 3:
        if topn == 3:
            tier = "Majority 3-0"
        elif topn == 2:
            tier = "Majority 2-1"
        else:
            tier = "Conflict (no majority)"
    elif k == 2:
        if topn == 2:
            tier = "Majority 2-0"
        else:
            tier = "Conflict (no majority)"
    else:
        tier = "Single label"
    # benchmark label: the modal label if unambiguous, else None
    has_majority = (topn * 2 > k) or (k == 1)
    bench = top if has_majority else None
    return (bench, tier, k, topn)

mv = W.apply(majority, axis=1, result_type="expand")
mv.columns = ["benchmark", "tier", "n_labels", "top_n"]
W = pd.concat([W, mv], axis=1)

tier_counts = W["tier"].value_counts().to_dict()
print("\nTier counts:")
for t in ["Majority 3-0", "Majority 2-1", "Majority 2-0", "Single label", "Conflict (no majority)", "No label"]:
    print(f"  {t:24s}: {tier_counts.get(t, 0)}")

print("\nPer-annotator labelled:")
for c in ["S", "R", "M"]:
    print(f"  {c}: {W[f'H_{c}'].notna().sum()}")

W.to_csv(os.path.join(DATA_DIR, "unified_labels.csv"), index_label="row")
print(f"\nSaved unified table -> data/unified_labels.csv ({len(W)} rows)")

# ---------------------------------------------------------------- metrics utils
def cohen_kappa(y1, y2, labels=None):
    y1 = np.asarray(y1)
    y2 = np.asarray(y2)
    if labels is None:
        labels = sorted(set(y1) | set(y2))
    idx = {l: i for i, l in enumerate(labels)}
    K = len(labels)
    O = np.zeros((K, K))
    for a, b in zip(y1, y2):
        O[idx[a], idx[b]] += 1
    n = O.sum()
    if n == 0:
        return float("nan")
    po = np.trace(O) / n
    r = O.sum(1) / n
    c = O.sum(0) / n
    pe = (r * c).sum()
    return float((po - pe) / (1 - pe)) if (1 - pe) != 0 else float("nan")

def accuracy_metric(y1, y2):
    y1 = np.asarray(y1)
    y2 = np.asarray(y2)
    return float(np.mean(y1 == y2)) if len(y1) else float("nan")

def macro_f1(y_true, y_pred, labels):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    f1s = []
    for l in labels:
        tp = np.sum((y_pred == l) & (y_true == l))
        fp = np.sum((y_pred == l) & (y_true != l))
        fn = np.sum((y_pred != l) & (y_true == l))
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        f1s.append(f1)
    return float(np.mean(f1s)) if f1s else float("nan")

def gwet_ac1(y1, y2, labels=None):
    y1 = np.asarray(y1)
    y2 = np.asarray(y2)
    if labels is None:
        labels = sorted(set(y1) | set(y2))
    K = len(labels)
    idx = {l: i for i, l in enumerate(labels)}
    O = np.zeros((K, K))
    for a, b in zip(y1, y2):
        O[idx[a], idx[b]] += 1
    n = O.sum()
    if n == 0:
        return float("nan")
    po = np.trace(O) / n
    pim = ((O.sum(0) + O.sum(1)) / (2 * n))
    pe = (pim * (1 - pim)).sum() / (K - 1)
    return float((po - pe) / (1 - pe)) if (1 - pe) != 0 else float("nan")

# Subsets
high = W[W.tier.isin(["Majority 3-0", "Majority 2-1"])]
med  = W[W.tier.isin(["Majority 3-0", "Majority 2-1", "Majority 2-0"])]
print(f"\nHighConf n={len(high)}; MedConf n={len(med)}")

MODELS = list(AI_FILES.keys())

def eval_table(sub):
    out = {}
    for m in MODELS:
        d = sub[sub[f"AI_{m}"].notna() & sub["benchmark"].notna()]
        yb = d["benchmark"].values
        yp = d[f"AI_{m}"].values
        out[m] = dict(
            n=int(len(d)),
            accuracy=round(accuracy_metric(yb, yp), 3),
            cohen_kappa=round(cohen_kappa(yb, yp, SIXCLASS), 3),
            gwet_ac1=round(gwet_ac1(yb, yp, SIXCLASS), 3),
            macro_f1_6=round(macro_f1(yb, yp, SIXCLASS), 3),
            macro_f1_present=round(macro_f1(yb, yp, [l for l in SIXCLASS if l in set(yb)]), 3)
        )
    return out

print("\n=== Table 3 (HighConf) ===")
t3 = eval_table(high)
for m, v in t3.items():
    print(f"  {m:18s} n={v['n']} acc={v['accuracy']} k={v['cohen_kappa']} mF1_6={v['macro_f1_6']} mF1_present={v['macro_f1_present']}")

# ---- Bootstrapped CIs
def bootstrap_ci(yb, yp, fn, nboot=1000, labels=SIXCLASS):
    yb = np.asarray(yb)
    yp = np.asarray(yp)
    n = len(yb)
    if n == 0:
        return (float("nan"), float("nan"))
    vals = []
    for _ in range(nboot):
        idx = RNG.integers(0, n, n)
        vals.append(fn(yb[idx], yp[idx], labels) if fn in (cohen_kappa, gwet_ac1) else fn(yb[idx], yp[idx]))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return (round(float(lo), 3), round(float(hi), 3))

def present_labels(yb):
    return [l for l in SIXCLASS if l in set(np.asarray(yb))]

def full_eval(sub, name_subset):
    rows = {}
    for m in MODELS:
        d = sub[sub[f"AI_{m}"].notna() & sub["benchmark"].notna()]
        yb = d["benchmark"].values
        yp = d[f"AI_{m}"].values
        pl = present_labels(yb)
        k_ci  = bootstrap_ci(yb, yp, cohen_kappa)
        a_ci  = bootstrap_ci(yb, yp, accuracy_metric)
        # Macro-F1 over present classes
        mf = []
        for _ in range(1000):
            ii = RNG.integers(0, len(yb), len(yb))
            mf.append(macro_f1(yb[ii], yp[ii], pl))
        mf_ci = (round(float(np.percentile(mf, 2.5)), 3), round(float(np.percentile(mf, 97.5)), 3))
        rows[m] = dict(
            n=int(len(d)),
            accuracy=round(accuracy_metric(yb, yp), 3),
            accuracy_ci=a_ci,
            cohen_kappa=round(cohen_kappa(yb, yp, SIXCLASS), 3),
            cohen_kappa_ci=k_ci,
            gwet_ac1=round(gwet_ac1(yb, yp, SIXCLASS), 3),
            gwet_ac1_ci=bootstrap_ci(yb, yp, gwet_ac1),
            macro_f1=round(macro_f1(yb, yp, pl), 3),
            macro_f1_ci=mf_ci,
            macro_f1_classes=len(pl),
            present_classes=pl
        )
    return rows

HIGH = full_eval(high, "HighConf")
MED  = full_eval(med, "MedConf")

# ---- Per-class metrics
def per_class(sub, m):
    d = sub[sub[f"AI_{m}"].notna() & sub["benchmark"].notna()]
    yb = d["benchmark"].values
    yp = d[f"AI_{m}"].values
    out = {}
    for l in SIXCLASS:
        tp = int(np.sum((yp == l) & (yb == l)))
        fp = int(np.sum((yp == l) & (yb != l)))
        fn = int(np.sum((yp != l) & (yb == l)))
        sup = int(np.sum(yb == l))
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        if sup > 0:
            out[l] = dict(precision=round(p, 3), recall=round(r, 3), f1=round(f1, 3), support=sup)
    return out

pc_gpt_high = per_class(high, "GPT-5 Full")

# ---- Triple-labelled subset
triple = W[W.n_labels == 3]
TRIPLE = full_eval(triple[triple.benchmark.notna()], "Triple")

# ---- Subset definitions
n_labelled = int(W[["H_S", "H_R", "H_M"]].notna().any(axis=1).sum())
n_reason_R = int(W["reason_excl_R"].notna().sum())

# ---- Confidence Calibration (normalised)
def normalise_conf(series):
    v = series.astype(float)
    lo, hi = v.min(), v.max()
    return (v - lo) / (hi - lo) if hi > lo else v * 0 + 0.5

cal_subset = W[W.benchmark.notna()].copy()
ece_results = {}
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
for ax, m in zip(axes.ravel(), MODELS):
    d = cal_subset[cal_subset[f"AI_{m}"].notna()].copy()
    conf = normalise_conf(d[f"CONF_{m}"]).values
    correct = (d[f"AI_{m}"].values == d["benchmark"].values).astype(float)
    bins = np.linspace(0, 1, 11)
    ece = 0.0
    xs = []
    ys = []
    for i in range(10):
        msk = (conf >= bins[i]) & (conf < bins[i+1] if i < 9 else conf <= bins[i+1])
        if msk.sum() == 0:
            continue
        acc = correct[msk].mean()
        cf = conf[msk].mean()
        w = msk.sum() / len(conf)
        ece += abs(acc - cf) * w
        xs.append(cf)
        ys.append(acc)
    ece_results[m] = round(float(ece), 3)
    ax.plot([0, 1], [0, 1], "--", color="gray", lw=1)
    ax.plot(xs, ys, "o-", color="#1f77b4")
    ax.set_title(f"{m} (ECE={ece:.3f})")
    ax.set_xlabel("Mean predicted confidence (norm.)")
    ax.set_ylabel("Empirical accuracy")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
plt.suptitle("Confidence calibration by model (HighConf+MedConf benchmark, per-model min-max norm.)")
plt.tight_layout()
plt.savefig(os.path.join(FIGS_DIR, "figure13_calibration.png"), dpi=150)
plt.close()

# ---- Pairwise kappa & dendrogram
agents = MODELS + ["Human (majority)"]
km = W[W.benchmark.notna()].copy()
mat = np.ones((len(agents), len(agents)))
for i, a in enumerate(agents):
    for j, b in enumerate(agents):
        if i < j:
            d = km.copy()
            ca = d["benchmark"] if a == "Human (majority)" else d[f"AI_{a}"]
            cb = d["benchmark"] if b == "Human (majority)" else d[f"AI_{b}"]
            msk = ca.notna() & cb.notna()
            k = cohen_kappa(ca[msk].values, cb[msk].values, SIXCLASS)
            mat[i, j] = mat[j, i] = k
dist = 1 - mat
np.fill_diagonal(dist, 0.0)
Z = linkage(squareform(dist, checks=False), method="average")
plt.figure(figsize=(8, 5))
dendrogram(Z, labels=agents, leaf_rotation=30)
plt.title("Hierarchical clustering of agents (distance = 1 − Cohen's κ)")
plt.ylabel("1 − κ")
plt.tight_layout()
plt.savefig(os.path.join(FIGS_DIR, "figure14_dendrogram.png"), dpi=150)
plt.close()

pd.DataFrame(mat, index=agents, columns=agents).round(3).to_csv(os.path.join(DATA_DIR, "pairwise_kappa.csv"))

# ---------------------------------------------------------------- save results JSON
results = dict(
    meta=dict(
        date="2026-05-29",
        data_mode="full",
        n_records=N,
        alignment=match_rates
    ),
    tier_counts=tier_counts,
    annot_counts={c: int(W[f'H_{c}'].notna().sum()) for c in ["S", "R", "M"]},
    subsets=dict(
        n_highconf=len(high),
        n_medconf=len(med),
        n_triple=int(len(triple)),
        n_triple_majority=int(triple.benchmark.notna().sum()),
        n_at_least_one_label=n_labelled,
        n_reason_excl_R=n_reason_R
    ),
    item9_10_11_highconf=HIGH,
    item9_10_11_medconf=MED,
    item11_perclass_gpt5full_highconf=pc_gpt_high,
    item12_triple=TRIPLE,
    item13_ece=ece_results,
    item17_pairwise_kappa={a: {b: round(float(mat[i, j]), 3) for j, b in enumerate(agents)} for i, a in enumerate(agents)}
)
with open(os.path.join(DATA_DIR, "results.json"), "w") as f:
    json.dump(results, f, indent=2)

print("\n=== Saved results.json ===")
