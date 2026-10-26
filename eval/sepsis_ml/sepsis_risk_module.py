"""Hemoglyph companion module — interpretable sepsis RISK PREDICTION (not diagnosis).

Design (user decision 2026-10-26, 'path C'): the guideline rule engine stays untrained; sepsis onset is an
outcome, so a separate, transparent, supervised model is trained ONCE on PhysioNet/CinC 2019 set A
(the development set already used for the SIRS/qSOFA rules) and evaluated on the untouched sets B and B2.
Output = hourly risk score with the contributing features (signed logistic contributions), labelled
'predictive, not diagnostic'. Nothing here feeds back into the rule engine.

Features: last-observation-carried-forward vitals and labs, 6-h and 12-h trends of vitals, hours since
ICU admission, age, sex, measurement-availability flags. Models: L2 logistic regression (fully
inspectable coefficients) and a monotone-free HistGradientBoosting as the accuracy reference.
Metrics: hourly AUROC/AUPRC, patient-level AUROC (max score before onset / all hours for negatives),
and the official PhysioNet 2019 utility score (early window −12 h, optimal +0 .. +3 h) at the
threshold chosen on set A only. Horizons: AUROC of the score at 6/12/24 h before onset.
"""
import sys, os, json, gzip, time, numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, average_precision_score
ROOT = "/home/user/Hemoglyph"; OUT = f"{ROOT}/eval/results/sepsis_ml"; os.makedirs(OUT, exist_ok=True)
SETS = {"A": f"{ROOT}/eval/realdata/sepsis2019/training_setA_sub5000.csv.gz",
        "B": f"{ROOT}/eval/quarantine/sepsis2019_setB/training_setB_sub5000.csv.gz",
        "B2": f"{ROOT}/eval/quarantine_v15/sepsis2019_setB2/training_setB2_sub5000.csv.gz"}
VIT = ["HR", "Temp", "SBP", "MAP", "Resp", "SaO2"]
LAB = ["WBC", "Lactate", "Creatinine", "Platelets", "Bilirubin_total", "BUN", "Glucose", "HCO3", "pH", "PaCO2", "BaseExcess", "Potassium", "Hgb", "PTT", "FiO2"]

def featurise(df):
    df = df.sort_values(["pid", "ICULOS"]).copy()
    g = df.groupby("pid", sort=False)
    X = pd.DataFrame(index=df.index)
    for c in VIT + LAB:
        ff = g[c].ffill()
        X[c] = ff
        X[c + "_miss"] = df[c].isna().astype(np.int8)
    for c in VIT + ["WBC", "Lactate", "Creatinine", "Platelets"]:
        ff = g[c].ffill()
        X[c + "_d6"] = ff - ff.groupby(df["pid"]).shift(6)
        X[c + "_d12"] = ff - ff.groupby(df["pid"]).shift(12)
        X[c + "_max12"] = ff.groupby(df["pid"]).rolling(12, min_periods=1).max().reset_index(level=0, drop=True) if c in ("HR", "Resp", "Temp", "Lactate", "WBC", "Creatinine") else 0.0
        X[c + "_min12"] = ff.groupby(df["pid"]).rolling(12, min_periods=1).min().reset_index(level=0, drop=True) if c in ("SBP", "MAP", "SaO2", "Platelets", "Temp") else 0.0
    # guideline-flavoured derived flags (transparent): SIRS components, qSOFA components, shock index
    X["sirs_hr"] = (X["HR"] > 90).astype(float); X["sirs_rr"] = (X["Resp"] > 20).astype(float)
    X["sirs_temp"] = ((X["Temp"] > 38) | (X["Temp"] < 36)).astype(float); X["sirs_wbc"] = ((X["WBC"] > 12) | (X["WBC"] < 4)).astype(float)
    X["qsofa_sbp"] = (X["SBP"] <= 100).astype(float); X["qsofa_rr"] = (X["Resp"] >= 22).astype(float)
    X["shock_index"] = X["HR"] / X["SBP"]
    X["lactate_hi"] = (X["Lactate"] >= 2).astype(float)
    X["Age"] = df["Age"]; X["male"] = (df["Gender"] == 1).astype(float); X["ICULOS"] = df["ICULOS"]
    X["HospAdmTime"] = df["HospAdmTime"].fillna(0)
    X = X.replace([np.inf, -np.inf], np.nan)
    return X, df

def onset_hour(df):
    """first hour with SepsisLabel==1 per pid (label is already shifted 6 h early by the challenge)"""
    o = df[df.SepsisLabel == 1].groupby("pid")["ICULOS"].min()
    return o

def utility(df, pred, dt_early=-12, dt_opt=-6, dt_late=3, max_u_tp=1, min_u_fn=-2, u_fp=-0.05, u_tn=0):
    """Official PhysioNet/CinC 2019 utility (Reyna et al. 2020), normalised against inaction/perfect."""
    tot = 0.0; best = 0.0; inact = 0.0
    for pid, g in df.assign(pred=pred).groupby("pid", sort=False):
        lab = g.SepsisLabel.values; p = g.pred.values; n = len(lab)
        if lab.any():
            t_s = int(np.argmax(lab)) + 6  # t_sepsis = first label hour + 6 (label shifted early)
            u = np.zeros(n); ub = np.zeros(n)
            for t in range(n):
                rel = t - t_s
                if p[t]:
                    if rel < dt_early: u[t] = u_fp
                    elif rel <= dt_opt: u[t] = max_u_tp * (rel - dt_early) / (dt_opt - dt_early)
                    elif rel <= dt_late: u[t] = max_u_tp * (1 - (rel - dt_opt) / (dt_late - dt_opt))
                    else: u[t] = 0
                else:
                    if rel < dt_early: u[t] = u_tn
                    elif rel <= dt_opt: u[t] = 0
                    elif rel <= dt_late: u[t] = min_u_fn * (rel - dt_opt) / (dt_late - dt_opt)
                    else: u[t] = min_u_fn
                # best: predict 1 from dt_early onward
                if rel >= dt_early:
                    ub[t] = max_u_tp * (rel - dt_early) / (dt_opt - dt_early) if rel <= dt_opt else (max_u_tp * (1 - (rel - dt_opt) / (dt_late - dt_opt)) if rel <= dt_late else 0)
                else: ub[t] = u_tn
            tot += u.sum(); best += ub.sum()
            inact += sum((min_u_fn * (t - t_s - dt_opt) / (dt_late - dt_opt)) if dt_opt < t - t_s <= dt_late else (min_u_fn if t - t_s > dt_late else 0) for t in range(n))
        else:
            tot += (p * u_fp).sum(); best += 0; inact += 0
    return (tot - inact) / (best - inact) if best != inact else float("nan")

def patient_auc(df, score):
    s = pd.Series(score, index=df.index)
    rows = []
    for pid, g in df.groupby("pid", sort=False):
        if g.SepsisLabel.any():
            pre = g[g.SepsisLabel == 0]  # hours before the (shifted) label
            rows.append((1, s[pre.index].max() if len(pre) else s[g.index].iloc[0]))
        else:
            rows.append((0, s[g.index].max()))
    y = np.array([r[0] for r in rows]); x = np.array([r[1] for r in rows])
    return roc_auc_score(y, x), int(y.sum()), int(len(y) - y.sum())

def horizon_auc(df, score, h):
    """score at h hours before onset (positives) vs a random hour for negatives"""
    s = pd.Series(score, index=df.index); rng = np.random.default_rng(1); pos = []; neg = []
    on = onset_hour(df)
    for pid, g in df.groupby("pid", sort=False):
        if pid in on.index:
            t = on[pid] + 6 - h  # t_sepsis − h
            row = g[g.ICULOS == t]
            if len(row): pos.append(s[row.index[0]])
        else:
            neg.append(s[g.index[rng.integers(len(g))]])
    return (roc_auc_score([1] * len(pos) + [0] * len(neg), pos + neg), len(pos), len(neg)) if pos else (float("nan"), 0, len(neg))

def main():
    t0 = time.time(); res = {}; lines = ["# Sepsis risk module — interpretable supervised companion (trained once on set A; evaluated on untouched B and B2)", ""]
    A = pd.read_csv(SETS["A"]); XA, A = featurise(A); yA = A.SepsisLabel.values
    cols = XA.columns.tolist(); med = XA.median(numeric_only=True)
    lr = make_pipeline(StandardScaler(), LogisticRegression(C=0.05, max_iter=2000, class_weight="balanced"))
    lr.fit(XA.fillna(med), yA)
    gb = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_depth=4, max_leaf_nodes=15, min_samples_leaf=300, l2_regularization=5.0, class_weight="balanced", early_stopping=True, validation_fraction=0.15, n_iter_no_change=20, random_state=0)
    gb.fit(XA, yA)
    # threshold for utility chosen on set A only (grid on predicted-probability quantiles)
    pA_lr = lr.predict_proba(XA.fillna(med))[:, 1]; pA_gb = gb.predict_proba(XA)[:, 1]
    def best_thr(p):
        best = (-9, None)
        for q in np.linspace(0.80, 0.99, 20):
            thr = np.quantile(p, q); u = utility(A, (p >= thr).astype(int))
            if u > best[0]: best = (u, thr)
        return best
    uA_lr, thr_lr = best_thr(pA_lr); uA_gb, thr_gb = best_thr(pA_gb)
    res["train"] = dict(n_rows=int(len(A)), n_pid=int(A.pid.nunique()), n_sepsis_pid=int(onset_hour(A).size), thr_lr=float(thr_lr), thr_gb=float(thr_gb), utility_A_lr=float(uA_lr), utility_A_gb=float(uA_gb))
    coef = lr[-1].coef_[0]; order = np.argsort(-np.abs(coef))[:20]
    lines += ["## Logistic model — 20 largest standardised coefficients (signed; fully inspectable)", "", "| feature | coefficient |", "|---|---:|"] + [f"| {cols[i]} | {coef[i]:+.3f} |" for i in order] + [""]
    res["coef_top20"] = {cols[i]: float(coef[i]) for i in order}
    lines += ["## Held-out performance", "", "| set | model | hourly AUROC | hourly AUPRC | patient AUROC (n sepsis / n no) | AUROC at −6 h / −12 h / −24 h | utility (thr from A) |", "|---|---|---|---|---|---|---|"]
    for name in ["A", "B", "B2"]:
        D = pd.read_csv(SETS[name]) if name != "A" else A
        X, D = featurise(D) if name != "A" else (XA, A)
        y = D.SepsisLabel.values
        for mname, p in [("logistic", lr.predict_proba(X.fillna(med))[:, 1]), ("gradient boosting", gb.predict_proba(X)[:, 1])]:
            thr = thr_lr if mname == "logistic" else thr_gb
            pa, ns, nn = patient_auc(D, p); h6 = horizon_auc(D, p, 6); h12 = horizon_auc(D, p, 12); h24 = horizon_auc(D, p, 24)
            u = utility(D, (p >= thr).astype(int))
            r = dict(hourly_auroc=float(roc_auc_score(y, p)), hourly_auprc=float(average_precision_score(y, p)), patient_auroc=float(pa), n_sepsis=ns, n_neg=nn,
                     auroc_h6=float(h6[0]), auroc_h12=float(h12[0]), auroc_h24=float(h24[0]), utility=float(u))
            res[f"{name}_{mname}"] = r
            lines.append(f"| {name}{' (development)' if name=='A' else ' (held out)'} | {mname} | {r['hourly_auroc']:.3f} | {r['hourly_auprc']:.3f} | {pa:.3f} ({ns} / {nn}) | {h6[0]:.3f} / {h12[0]:.3f} / {h24[0]:.3f} | {u:.3f} |")
            print(name, mname, r, flush=True)
    lines += ["", "Hourly AUROC = every ICU hour as a unit (challenge framing). Patient AUROC = maximum score over hours before the shifted label for septic patients vs maximum over all hours for non-septic patients (closest to the engine's per-patient 'prediction frame'). Horizon AUROC = score exactly h hours before t_sepsis vs a random hour of each non-septic patient. Utility = official PhysioNet/CinC 2019 normalised utility (Reyna 2020), alert threshold fixed on set A. Inputs are the 5,000-patient public subsets used throughout the paper; the rule engine's own sepsis score on the same sets was 0.600 / 0.610 / 0.588 (patient-level, labs only).",
              "", "This module is a predictive risk score, not a diagnosis; it is trained on outcome labels and therefore sits outside the untrained guideline engine. It is reported with its contributing features so that every alert can be inspected.", f"", f"Runtime {time.time()-t0:.0f} s."]
    open(f"{OUT}/sepsis_ml_report.md", "w").write("\n".join(lines) + "\n"); json.dump(res, open(f"{OUT}/sepsis_ml_summary.json", "w"), indent=1)
    import pickle; pickle.dump(dict(cols=cols, median=med, lr=lr, gb=gb, thr_lr=thr_lr, thr_gb=thr_gb), gzip.open(f"{OUT}/sepsis_risk_models.pkl.gz", "wb"))
    print("\n".join(lines))

if __name__ == "__main__":
    main()
