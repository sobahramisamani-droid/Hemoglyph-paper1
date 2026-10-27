"""R4 → R5: condense the main text for JBI (target ≈ 5,000 words Introduction–Conclusion).

Moves, verbatim, to the Supplement: §2.7 (post-freeze v8) → Note 9; §3.6 (external cohorts) → Note 10; §3.9 (calibration,
subgroups, robustness) → Note 11. Shortens the duplicated system description in §3.1 and one Discussion paragraph.
No number is changed; every moved passage is kept word-for-word in the Supplement.
"""
import re

SRC, DST = "Paper1_Hemoglyph_JBI_EN_v7_R4.md", "Paper1_Hemoglyph_JBI_EN_v7_R5.md"
s = open(SRC, encoding="utf-8").read()


def take(heading_prefix, next_pattern):
    """Return (block_text, body_without_block) for the section starting with heading_prefix."""
    m = re.search(r"^### " + re.escape(heading_prefix) + r"[^\n]*\n", s, re.M)
    assert m, heading_prefix
    nxt = re.compile(next_pattern, re.M).search(s, m.end())
    return s[m.start():nxt.start()], (m.start(), nxt.start())


moved = []
# ---- §2.7 → Note 9
blk, (a, b) = take("2.7 ", r"^### 2\.8 ")
stub = ("### 2.7 Post-freeze development version (v8)\n\nAfter the freeze, twelve review-driven improvement proposals were tested against the frozen artefacts before any code was "
        "changed; the procedure, the four supported and eight refuted proposals, and the resulting development version v8 are "
        "described in Supplementary Note 9. No frozen number in this paper derives from v8.\n\n")
moved.append(("Supplementary Note 9 — Post-freeze development version (v8); moved verbatim from the main text", blk.split("\n", 1)[1]))
s = s[:a] + stub + s[b:]

# ---- §3.6 → Note 10
blk, (a, b) = take("3.6 ", r"^### 3\.7 ")
stub = ("### 3.6 External cohorts and case reports\n\nOn the UCI thyroid referral set AUROC was 0.979 (0.974–0.983) for hypothyroidism and 0.798 (0.783–0.814) for hyperthyroidism; "
        "on the HCV cohort 0.925 (0.881–0.962) for any liver disease; on ILPD 0.704 (0.661–0.747); in the MIMIC-IV demo top-5/10 recall was "
        "47.5/62.1% (v7 re-run); on 50 PMC case reports the specific diagnosis was in the top five in 26% and the correct syndrome in 68% "
        "(Table 2; full results in Supplementary Note 10).\n\n")
moved.append(("Supplementary Note 10 — External cohorts and case reports; moved verbatim from the main text", blk.split("\n", 1)[1]))
s = s[:a] + stub + s[b:]

# ---- §3.9 → Note 11
blk, (a, b) = take("3.9 ", r"^### 3\.10 ")
first = blk.split("\n\n")[1]
assert "AUROC was 0.797" in first
stub = ("### 3.9 Calibration, subgroups and robustness\n\n"
        "Raw scores were uncalibrated (pooled AUROC 0.797; reliability and decision curves before and after cross-fitted isotonic regression in Fig. 7); "
        "subgroup recall by age, sex and unit type, unit-invariance and perturbation results are given in Supplementary Note 11 and Table S4.\n\n")
moved.append(("Supplementary Note 11 — Calibration, subgroups and robustness; moved verbatim from the main text", blk.split("\n", 1)[1]))
s = s[:a] + stub + s[b:]

# ---- §3.1: drop the paragraph that repeats §2.1; keep the operational facts
old31 = s[s.index("### 3.1 System and knowledge base"):s.index("### 3.2 ")]
p1_start = old31.index("Hemoglyph is a single-process Python engine (Fig. 1).")
p1_end = old31.index("\n\n", p1_start)
new_p1 = ("The architecture (Fig. 1; Section 2.1) was frozen as engine v7 with registry 14.1.0 (33,183 executable rules: 272 hand-curated anchors and "
          "32,911 AI-drafted, unaudited candidates from 785 guideline sources; ~900 curated syndrome constellations). The engine is deterministic "
          "(byte-identical output in 50/50 repeated stays), runs on one CPU core in ~1 s per panel and makes no network calls. Open and proprietary "
          "components are tabulated in Supplementary Table S15; only the open components were evaluated.")
new31 = old31[:p1_start] + new_p1 + old31[p1_end:]
s = s.replace(old31, new31)

# ---- Discussion: the post-freeze proposals are now Note 9; keep the verification reframing
old_d = ("After the freeze, twelve review-driven improvement proposals were tested against the frozen artefacts before any code was changed "
         "(Supplementary Note 7; Methods). Four were supported—confidence bands, re-sourcing of 28 rules, MELD-Na/PLR indices and a separate supervised "
         "sepsis companion (held-out patient-level AUROC 0.654/0.631 versus the engine's 0.610/0.588)—and the rest were refuted: adaptive truncation traded "
         "precision for recall almost one-for-one, and the ketoacidosis misses were missing criteria, not covering suppression. The verification results reframe")
assert s.count(old_d) == 1, "discussion anchor"
s = s.replace(old_d, ("Post-freeze proposals were tested against the frozen artefacts before any code changed (Section 2.7; Supplementary Notes 7 and 9); "
                      "a separate supervised sepsis companion reached held-out AUROC 0.654/0.631 versus the engine's 0.610/0.588. The verification results reframe"))

# ---- append moved notes to the Supplementary section
notes = "\n\n".join(f"### {title}\n\n{body.strip()}" for title, body in moved)
s = s.rstrip() + "\n\n" + notes + "\n"
s = s.replace("Revision R4 (2026-10-27)", "Revision R5 (2026-10-27)")
# ---- Table 3 (data sources) lost its only main-text citation with §2.7; cite it where the datasets are introduced
anchor = "### 2.4 Datasets and reference standards\n\n"
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + "Data sources, reference standards and their roles are summarised in Table 3. ")

# ---- renumber tables by first appearance in the condensed main text (one pass, captions and cross-references together)
main = s.split("## Tables")[0]
order = []
for m in re.finditer(r"Table (\d)\b(?!\d)", main):
    if int(m.group(1)) not in order:
        order.append(int(m.group(1)))
order += [n for n in range(1, 6) if n not in order]
tmap = {o: n for n, o in enumerate(order, 1)}
head, tail = s.split("## Tables", 1)
tables_block, supp_block = tail.split("## Supplementary information", 1)
sub = lambda txt: re.sub(r"Table (\d)\b(?!\d)", lambda m: f"Table {tmap[int(m.group(1))]}", txt)
blocks = [b.strip() for b in re.split(r"(?=^\*\*Table \d \| )", tables_block.strip(), flags=re.M) if b.strip()]
assert len(blocks) == 5
blocks = sorted((sub(b) for b in blocks), key=lambda b: int(re.match(r"\*\*Table (\d)", b).group(1)))
s = sub(head) + "## Tables\n\n" + "\n\n".join(blocks) + "\n\n## Supplementary information" + sub(supp_block)
print("table renumbering R5:", tmap)

open(DST, "w", encoding="utf-8").write(s)

body = s.split("## References")[0]
core = body[body.index("## 1. Introduction"):body.index("## CRediT")]
print("Introduction–Conclusion words:", len(re.sub(r"\|.*", "", core).split()))
print("Fig/Table first-cite check:", sorted(set(re.findall(r"Fig\. (\d)", core))), sorted(set(re.findall(r"Table (\d)\b", core))))
