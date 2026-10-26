"""Round-4 part B: replace NHANES 2017-18 (J) values, which had come from registry 14.0.0, with the frozen-v7 re-run."""
import json, re, pathlib, sys
R = pathlib.Path("/home/user/Hemoglyph")
S = json.load(open(R / "eval/results/nhanes_2017/summary_v7.json"))
rep = open(R / "eval/results/nhanes_2017/report_v7.md").read()
m = re.search(r"(\d+) participants had every core analyte inside its reference interval; (\d+) \(", rep)
n_healthy, n_false = int(m.group(1)), int(m.group(2))
def a(k): return f"{S[k]['auroc']:.3f}"
NEW = {k: a(k) for k in ["diabetes","ckd","anemia","iron_deficiency","hyperuricemia","hypercholesterolemia","alt_elevation","diabetes_selfreport","ckd_selfreport"]}
OLD = {"diabetes":"0.945","ckd":"0.958","anemia":"0.973","iron_deficiency":"0.990","hyperuricemia":"0.943","hypercholesterolemia":"0.902","alt_elevation":"0.721","diabetes_selfreport":"0.918","ckd_selfreport":"0.816"}
HI = {"diabetes":("0.938","0.924"),"ckd":("0.968","0.962"),"anemia":("0.994","0.983"),"iron_deficiency":("–","0.972"),"hyperuricemia":("0.958","0.955"),"hypercholesterolemia":("0.883","0.886"),"alt_elevation":("0.880","0.877"),"diabetes_selfreport":("0.914","0.898"),"ckd_selfreport":("0.748","0.799")}
print("J v7:", NEW, "healthy", n_false, "/", n_healthy)
six = [float(NEW[k]) for k in ["diabetes","ckd","anemia","iron_deficiency","hyperuricemia","hypercholesterolemia"]]
hi6 = [0.938,0.924,0.968,0.962,0.994,0.983,0.972,0.958,0.955,0.883,0.886]
lo, hi = min(six+hi6), max(six+hi6)
alt = sorted([float(NEW["alt_elevation"]),0.880,0.877])
tot_false = n_false + 1 + 0; tot_n = n_healthy + 246 + 79

files = [R/"docs/paper1/v7/Paper1_Hemoglyph_npj_EN_v7_R1.md", R/"docs/paper1/v7/Paper1_Hemoglyph_SampleStyle_v7_R1.md", R/"docs/paper1/supplement/SUPPLEMENT_R1.md", R/"docs/paper1/v7/make_paper_src_figs.py"]
log = []
for f in files:
    t = f.read_text(encoding="utf-8"); t0 = t
    for k, o in OLD.items():
        h, i = HI[k]
        for sep in ["/", " / "]:
            old = f"{o}{sep}{h}{sep}{i}"; new = f"{NEW[k]}{sep}{h}{sep}{i}"
            c = t.count(old)
            if c: t = t.replace(old, new); log.append((f.name, old, new, c))
    # figure data list
    if f.name.endswith(".py"):
        old = "J=[0.945,0.958,0.973,0.990,0.902,0.943,0.721]"
        assert t.count(old) == 1
        t = t.replace(old, "J=[%s]" % ",".join(NEW[k] for k in ["diabetes","ckd","anemia","iron_deficiency","hypercholesterolemia","hyperuricemia","alt_elevation"]))
        t = t.replace('ax.set_ylim(0.6,1.0); ax.set_ylabel("AUROC")', 'ax.set_ylim(0.5,1.0); ax.set_ylabel("AUROC (axis truncated at 0.5)")')
        t = t.replace('label="2017–18 (J, development)"', 'label="2017–18 (J, development; v7 re-run)"')
    # healthy counts
    for old, new in [("1/160, 1/246 and 0/79 (2/485", f"{n_false}/{n_healthy}, 1/246 and 0/79 ({tot_false}/{tot_n}"),
                     ("1/246, 0/79, 1/160 (2/485)", f"1/246, 0/79, {n_false}/{n_healthy} ({tot_false}/{tot_n})"),
                     ("with 2 false assertions among 485 healthy adults", f"with {tot_false} false assertions among {tot_n} healthy adults"),
                     ("(2/485, 0.4%;", f"({tot_false}/{tot_n}, {100*tot_false/tot_n:.1f}%;"),
                     ("0.89–0.99 for six laboratory-defined targets, 0.71–0.88 for ALT elevation", f"{lo:.2f}–{hi:.2f} for six laboratory-defined targets, {alt[0]:.2f}–{alt[-1]:.2f} for ALT elevation"),
                     ]:
        c = t.count(old)
        if c: t = t.replace(old, new); log.append((f.name, old, new, c))
    # delete wrong explanations
    for old, new in [
        ("ALT elevation is the seventh pre-specified target and the weakest: the engine grades ALT against sex-specific ACG limits whereas the 2017–18 development label used a higher threshold that was corrected under Amendment 14, which is why that cycle is lower; it is reported in full rather than omitted",
         "ALT elevation is the seventh target (excluded a priori from the Amendment-15 criterion) and the weakest; it is reported in full rather than omitted. A correction: the previous version of this manuscript quoted 0.721 for 2017–18 and attributed it to a label-threshold change; on re-inspection that value came from a run of registry 14.0.0, not the frozen v7, and the label had not changed. All 2017–18 values above are from the v7 re-run"),
        (" (the lower 2017–18 value reflects a threshold definition corrected under Amendment 14)",
         " (correction: the 2017–18 column of the previous version had been taken from a registry-14.0.0 run and ALT was quoted as 0.721 with a wrong explanation; all 2017–18 values are now from the frozen-v7 re-run)"),
    ]:
        c = t.count(old)
        if c: t = t.replace(old, new); log.append((f.name, old[:40], "…", c))
    if t != t0: f.write_text(t, encoding="utf-8")
for l in log: print(l)
# remaining stale strings?
for f in files:
    t = f.read_text(encoding="utf-8")
    for k, o in OLD.items():
        for pat in [f"{o}/{HI[k][0]}", f"{o} / {HI[k][0]}"]:
            if pat in t: print("STALE", f.name, pat)
    if "0.721" in t: print("CHECK 0.721 in", f.name, [t[max(0,i-60):i+40] for i in [m.start() for m in re.finditer("0.721", t)]][:3])
