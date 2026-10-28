#!/usr/bin/env python3
"""LabPanel-Check — black-box conformance scorer for laboratory-panel readers (standard library only).

    python3 score.py READS.json [--second READS_run2.json] [--out card.json] [--label NAME]

READS.json : {panel_id: [{"name": str, "probability": float, "id"?: str, "tier"?: str}, ...]} in rank order,
             produced by ANY reader (rule engine, model, LLM) from panels.json.gz. Missing panel ids are reported, not
             silently skipped. A second file produced by an independent run scores P1 (determinism).
Output     : a conformance card (Markdown on stdout, JSON with --out). The card is descriptive; it has no pass/fail verdict
             beyond the per-property targets listed in spec.json.

The scorer never sees a clinical label; the only hidden information it uses is the P5 target group (which diagnosis lost
its defining analyte) and the P6 healthy / reference-positive flags, both derived from guideline criteria on the panels.
"""
from __future__ import annotations
import os, sys, json, gzip, re, argparse

HERE = os.path.dirname(os.path.abspath(__file__))


def load_json(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * ((p * (1 - p) + z * z / (4 * n)) / n) ** 0.5
    return ((c - h) / d, (c + h) / d)


class Scorer:
    def __init__(self, panels, label_map):
        self.panels = panels
        self.groups = {g: (set(v["entities"]), re.compile(v["regex"], re.I)) for g, v in label_map["groups"].items()}
        self.renal = set(label_map["renal_union"])
        self.redundant = label_map["p5_redundant"]
        self.benign = tuple(label_map["p6_benign_words"])
        self.detect = {k: tuple(v) for k, v in label_map["p6_detection"].items()}

    # ---- vocabulary mapping -------------------------------------------------------------------------------------------
    def group_ranks(self, entries):
        ranks = {}
        for rank, e in enumerate(entries[:10], 1):
            eid = str(e.get("id", "") or ""); name = str(e.get("name", "") or "")
            for g, (ents, rx) in self.groups.items():
                if (eid and eid in ents) or rx.search(name):
                    ranks.setdefault(g, rank)
        return ranks

    @staticmethod
    def top5(ranks):
        return {g for g, r in ranks.items() if r <= 5}

    @staticmethod
    def jaccard(a, b):
        return 1.0 if not a and not b else len(a & b) / len(a | b)

    # ---- properties ---------------------------------------------------------------------------------------------------
    def score(self, reads, reads2=None):
        card, missing = {}, sorted(pid for pid in self.panels if pid not in reads)
        by_prop = {}
        for pid, rec in self.panels.items():
            by_prop.setdefault(rec["property"], []).append(pid)

        # P1 determinism
        if reads2 is not None:
            same = sum(json.dumps(reads.get(p), sort_keys=True) == json.dumps(reads2.get(p), sort_keys=True) for p in self.panels)
            card["P1_determinism"] = {"identical": same, "n": len(self.panels)}

        # P2 / P3 invariance against the conventional reference
        for prop, key in (("P2", "P2_unit_invariance"), ("P3", "P3_presentation_invariance")):
            js, diff = [], []
            for pid in by_prop.get(prop, []):
                ref = self.panels[pid]["reference"]
                if pid in reads and ref in reads:
                    a, b = self.top5(self.group_ranks(reads[pid])), self.top5(self.group_ranks(reads[ref]))
                    js.append(self.jaccard(a, b))
                    if a != b:
                        diff.append({"id": pid, "only_perturbed": sorted(a - b), "only_reference": sorted(b - a)})
            card[key] = {"mean_jaccard": sum(js) / len(js) if js else None, "identical": sum(j == 1.0 for j in js), "n": len(js),
                         "non_identical_pairs": diff}

        # P4 monotonicity
        ladders = {}
        for pid in by_prop.get("P4", []):
            ladders.setdefault(self.panels[pid]["ladder_id"], []).append(pid)
        v = n = 0; violating = []
        for lid, pids in ladders.items():
            pids.sort(key=lambda p: self.panels[p]["ladder"])
            if not all(p in reads for p in pids):
                continue
            best = [min([self.group_ranks(reads[p]).get(g, 99) for g in self.renal]) for p in pids]
            n += 1
            if any(best[i + 1] > best[i] for i in range(len(best) - 1)):
                v += 1; violating.append(lid)
        card["P4_monotonicity"] = {"violations": v, "n": n, "violating_ladders": violating}

        # P5 absent analyte
        u = n = 0; su = sn = 0; detail = []
        for pid in by_prop.get("P5", []):
            if pid not in reads:
                continue
            rec = self.panels[pid]; g = rec["target_group"]
            unsupported = self.group_ranks(reads[pid]).get(g, 99) <= 5
            present = {it["analyte"] for it in rec["panel"]}
            red = sorted(set(self.redundant.get(rec["removed_analyte"], [])) & present)
            n += 1; u += int(unsupported)
            if not red:
                sn += 1; su += int(unsupported)
            if unsupported:
                detail.append({"id": pid, "target": g, "removed": rec["removed_analyte"], "redundant_present": red})
        card["P5_absent_analyte"] = {"unsupported": u, "n": n, "strict_unsupported": su, "strict_n": sn, "unsupported_panels": detail}

        # P6 healthy silence / reference detection
        fa = nh = 0; fa_list = []; det = {k: [0, 0] for k in self.detect}
        for pid in by_prop.get("P6", []):
            if pid not in reads:
                continue
            rec = self.panels[pid]; ents = reads[pid]
            asserted = [e for e in ents if float(e.get("probability", 0)) >= 0.5
                        and str(e.get("tier", "diagnosis")) == "diagnosis"
                        and not any(b in str(e.get("name", "")).lower() for b in self.benign)]
            if rec["healthy"]:
                nh += 1
                if asserted:
                    fa += 1; fa_list.append({"id": pid, "asserted": [str(e.get("name")) for e in asserted[:3]]})
            for k in rec["reference_positive"]:
                det[k][1] += 1
                det[k][0] += int(any(any(s in str(e.get("name", "")).lower() for s in self.detect[k]) and float(e.get("probability", 0)) >= 0.5 for e in ents))
        card["P6_healthy"] = {"false_assertions": fa, "n_healthy": nh, "false_assertion_panels": fa_list,
                              "detection": {k: {"detected": a, "n": b} for k, (a, b) in det.items()}}
        card["missing_panel_ids"] = missing
        return card


def render(card, label):
    L = [f"# LabPanel-Check conformance card — {label}", ""]
    L += ["| property | result | target |", "|---|---|---|"]
    if "P1_determinism" in card:
        c = card["P1_determinism"]; L.append(f"| P1 determinism: identical readings on two runs | {c['identical']}/{c['n']} | all |")
    for key, nm in (("P2_unit_invariance", "P2 unit invariance"), ("P3_presentation_invariance", "P3 presentation invariance")):
        c = card[key]
        if c["n"]:
            L.append(f"| {nm}: top-5 identical (mean Jaccard) | {c['identical']}/{c['n']} ({c['mean_jaccard']:.2f}) | all (1.00) |")
    c = card["P4_monotonicity"]; L.append(f"| P4 creatinine monotonicity: violating ladders | {c['violations']}/{c['n']} | 0 |")
    c = card["P5_absent_analyte"]
    L.append(f"| P5 unsupported assertion after removing the defining analyte | {c['unsupported']}/{c['n']} | 0 |")
    L.append(f"| P5 strict subset (no redundant analyte left) | {c['strict_unsupported']}/{c['strict_n']} | 0 |")
    c = card["P6_healthy"]
    lo, hi = wilson(c["false_assertions"], c["n_healthy"])
    L.append(f"| P6 healthy adults with a disease asserted at p ≥ 0.5 | {c['false_assertions']}/{c['n_healthy']} (95% CI {100*lo:.0f}–{100*hi:.0f}%) | 0 |")
    for k, d in c["detection"].items():
        L.append(f"| P6 detection of {k} at p ≥ 0.5 | {d['detected']}/{d['n']} | descriptive |")
    for key in ("P2_unit_invariance", "P3_presentation_invariance"):
        for d in card[key]["non_identical_pairs"]:
            L.append(f"- {d['id']}: only in perturbed top-5 {d['only_perturbed']}; only in reference top-5 {d['only_reference']}")
    if card["missing_panel_ids"]:
        L += ["", f"Missing readings for {len(card['missing_panel_ids'])} panel ids: " + ", ".join(card["missing_panel_ids"][:20]) + (" …" if len(card["missing_panel_ids"]) > 20 else "")]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reads"); ap.add_argument("--second"); ap.add_argument("--out"); ap.add_argument("--label", default="reader")
    ap.add_argument("--panels", default=os.path.join(HERE, "panels.json.gz")); ap.add_argument("--label-map", default=os.path.join(HERE, "label_map.json"))
    a = ap.parse_args()
    sc = Scorer(load_json(a.panels), load_json(a.label_map))
    card = sc.score(load_json(a.reads), load_json(a.second) if a.second else None)
    print(render(card, a.label))
    if a.out:
        json.dump(card, open(a.out, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
