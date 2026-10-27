"""R3 → R4: JBI house format.

Elsevier/JBI requirements applied (guide for authors, read 2026-10-27):
  highlights ≤ 85 characters each · structured abstract ≤ 300 words · 1–7 keywords · Statement of Significance table at the end
  of the Introduction (≤ 150 words) · numbered sections in the order Introduction / Material and methods / Results / Discussion /
  Conclusion · CRediT statement · declaration of generative AI · data statement · references numbered by first appearance ·
  tables numbered by first appearance.  The single-rater source audit is finalised (second rater: see Supplementary Note 8).
"""
import re

SRC = "Paper1_Hemoglyph_JBI_EN_v7_R3.md"
DST = "Paper1_Hemoglyph_JBI_EN_v7_R4.md"
s = open(SRC, encoding="utf-8").read()


def between(text, a, b):
    i = text.index(a)
    j = text.index(b, i + len(a))
    return text[i + len(a):j]


# ------------------------------------------------------------------ pieces of R3
title = s.splitlines()[0][2:].strip()
authors = between(s, "- Source-concordance audit", "## Abstract").split("\n", 1)[1].strip()
abstract_old = between(s, "## Abstract", "## Introduction").strip()
intro = between(s, "## Introduction", "## Results").strip()
results = between(s, "## Results", "## Discussion").strip()
discussion = between(s, "## Discussion", "## Methods").strip()
methods = between(s, "## Methods", "## Data availability").strip()
data_av = between(s, "## Data availability", "## Code availability").strip()
code_av = between(s, "## Code availability", "## Author contributions").strip()
competing = between(s, "## Competing interests", "## Use of artificial intelligence").strip()
ai_use = between(s, "## Use of artificial intelligence", "## Ethics").strip()
ethics = between(s, "## Ethics", "## References").strip()
refs = between(s, "## References", "## Figure legends").strip()
figlegs = between(s, "## Figure legends", "## Tables").strip()
tables = between(s, "## Tables", "## Supplementary information").strip()
supp = s.split("## Supplementary information", 1)[1].strip()

# ------------------------------------------------------------------ single-rater audit: final wording
old = ("Rater 1 was an AI agent (declared); a second, human\nnon-clinician rater and inter-rater agreement are pending and will be added before submission.")
assert old in results
results = results.replace(old, (
    "The audit was performed by a single declared rater (an AI agent under the first author's direction); a second, human "
    "non-clinician rater returned templated verdicts in a first round (agreement with rater 1 κ = 0.05) and that round was rejected "
    "and is archived with the protocol rather than averaged in (Supplementary Note 8). No inter-rater reliability is therefore "
    "claimed for the audit, and its two figures (92% unverifiable, ≥ 7.5% discordant) should be read as one rater's finding "
    "under a frozen protocol that anyone can re-run."))

# ------------------------------------------------------------------ highlights (≤ 85 characters)
highlights = [
    "Offline rule engine ranks a cited lab differential; every output traces to a source",
    "Property-based verification found a ranking defect missed by 353 vignettes",
    "Frozen one-shot evaluation on >20,000 encounters; a failed first round is reported",
    "Untrained engine at recall@5 parity with an unnamed frontier LLM, fully traceable",
    "Source audit: 92% of sampled rules not verifiable from their locators; limits stated",
]
for h in highlights:
    assert len(h) <= 85, (len(h), h)

# ------------------------------------------------------------------ structured abstract (≤ 300 words)
abstract = """**Objective.** To describe and evaluate Hemoglyph, an offline research-prototype engine that ranks a cited differential diagnosis from a structured laboratory panel using 33,183 guideline-transcribed executable rules (99.2% AI-drafted by a non-clinician author, not clinically audited) without outcome training, and to test whether such a knowledge base can be made verifiable and auditable.

**Methods.** Property-based tests run on every release. Under an internal, hash-frozen analysis plan with two one-shot quarantine rounds—the first failed its superiority criteria and the criteria were weakened to non-inferiority—the frozen engine was evaluated on the eICU-CRD demo (2,314 ICU stays), MIMIC-IV demo, 9,000 NHANES adults (three cycles), 14,420 sepsis patients and external cohorts. A blinded, paired comparison with an unnamed frontier large language model (LLM) used identical inputs on 400 stays. A pre-specified source-concordance audit sampled 200 rules.

**Results.** From laboratory values alone, 60.8% (95% CI 58.7–62.9) of clinician-listed ICU diagnoses appeared in the top five suggestions at precision@5 of 14.2% against an incomplete problem list; a prevalence baseline reached 51.3%, so the engine contributes ordering rather than coverage. NHANES AUROCs reproduced across cycles (0.88–0.99) with 2 false assertions among 485 healthy adults. Engine and LLM were at recall@5 parity (60.7% vs 59.6%, p = 0.54); the LLM led at rank 1 but was only moderately self-consistent (κ 0.69). Sepsis prediction failed as pre-specified. Ablation located the result in 272 hand-curated anchors and the syndrome layer, not the AI-drafted bulk. Property-based tests exposed one ranking defect that 353 vignettes missed. The source audit found 92% of sampled rules unverifiable from their locators and 7.5% demonstrably discordant.

**Conclusions.** A guideline-transcribed engine can match a frontier LLM on a blinded panel-interpretation task while remaining traceable, but provenance granularity—not rule count—is the binding constraint on the auditability of AI-drafted knowledge bases. No clinical claim is made; code and rules are public."""
nwords = len(re.sub(r"\*\*[^*]+\*\*", "", abstract).split())
assert nwords <= 300, nwords

keywords = "Clinical decision support; Laboratory medicine; Knowledge base; Rule-based systems; Verification; Large language models; Reproducibility"

significance = """**Statement of Significance**

| | |
|---|---|
| **Problem or issue** | Knowledge bases for laboratory-panel interpretation can now be drafted at scale with AI assistance, but their rules are rarely verifiable, their evaluations are seldom pre-specified, and comparisons with large language models are unstable and unauditable. |
| **What is already known** | Rule-based decision support is traceable but costly to build and maintain; LLMs scale but cannot cite the rule behind an output and drift between runs; most retrospective evaluations select metrics after seeing results. |
| **What this paper adds** | Executable invariants that caught a defect 353 vignettes missed; a hash-frozen one-shot evaluation whose failed first round is reported; a reproducible source-concordance audit with explicit denominators and an unfavourable result; a blinded paired LLM comparison at recall@5 parity. |
| **Who would benefit** | Informaticians building or auditing AI-drafted knowledge bases, evaluators of laboratory decision support, and laboratory-medicine services considering offline interpretive tools. |"""
sig_words = len(re.sub(r"\*\*[^*]+\*\*|\|", " ", significance.split("\n", 2)[2]).split())
assert sig_words <= 150, sig_words


# cite the three guideline references that R3 listed but never cited in the text (KDIGO, ADA, UDMI)
old_m = "KDIGO chronicity, UDMI acuity,"
assert methods.count(old_m) == 1
methods = methods.replace(old_m, "KDIGO chronicity [26], ADA glycaemic criteria [27], UDMI acuity [28],")

# ------------------------------------------------------------------ section numbering
def number(block, major):
    out, k = [], 0
    for line in block.split("\n"):
        if line.startswith("### "):
            k += 1
            line = f"### {major}.{k} {line[4:]}"
        out.append(line)
    return "\n".join(out)


# Discussion in R3 contains "### Limitations" and "### Conclusion"; Conclusion becomes section 5
disc_main = discussion.split("### Conclusion")[0].rstrip()
conclusion = discussion.split("### Conclusion")[1].strip()

credit = """**Sobhan Bahrami:** Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Writing – original draft, Writing – review & editing, Visualization, Project administration. **Zhaleh Tahmasebinejad:** Methodology (statistical analysis plan), Validation (review of the quarantine reporting), Writing – review & editing. **Ehsan Bahrami Samani:** Methodology (statistical supervision), Supervision, Writing – review & editing. All authors approved the final version. *(Contributions of Z.T. and E.B.S. to be confirmed by them before submission.)*"""

gen_ai = """During the preparation of this work the authors used AI-assisted tools in three declared ways: (i) the rule registry was drafted with AI assistance from guideline text and filtered by automated consistency audits (99.2% of records; stated throughout); (ii) an AI coding agent assisted with evaluation scripts, figure generation (data visualisations derived from the released outputs by reproducible code) and the blinded LLM arm under the first author's direction; (iii) the single-rater source-concordance audit was performed by an AI agent under a frozen protocol. All analyses were specified in the statistical analysis plan and are reproducible from the released code. After using these tools, the authors reviewed and edited the content as needed and take full responsibility for the content of the published article. No AI tool is listed as an author."""

body = "\n\n".join([
    f"# {title}",
    "*Original research article — methodological. Revision R4 (2026-10-27), formatted for the Journal of Biomedical Informatics. Research prototype — not approved or intended for clinical use.*",
    authors,
    "**Highlights**\n" + "\n".join(f"- {h}" for h in highlights),
    "## Abstract\n\n" + abstract,
    "**Keywords:** " + keywords,
    "## 1. Introduction\n\n" + intro + "\n\n" + significance,
    "## 2. Material and methods\n\n" + number(methods, 2),
    "## 3. Results\n\n" + number(results, 3),
    "## 4. Discussion\n\n" + number(disc_main, 4),
    "## 5. Conclusion\n\n" + conclusion,
    "## CRediT authorship contribution statement\n\n" + credit,
    "## Declaration of competing interest\n\n" + competing,
    "## Funding\n\nThis research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.",
    "## Declaration of generative AI and AI-assisted technologies in the writing process\n\n" + gen_ai,
    "## Ethics statement\n\n" + ethics,
    "## Data availability\n\n" + data_av + "\n\n" + code_av,
    "## References\n\n" + refs,
    "## Figure legends\n\n" + figlegs,
    "## Tables\n\n" + tables,
    "## Supplementary information\n\n" + supp,
])

# ------------------------------------------------------------------ references: renumber by first appearance (main text order)
main_text = body.split("## References")[0]


def expand(tok):
    nums = []
    for part in re.split(r",\s*", tok):
        if "–" in part or "-" in part:
            a, b = re.split(r"[–-]", part)
            nums.extend(range(int(a), int(b) + 1))
        else:
            nums.append(int(part))
    return nums


order = []
for m in re.finditer(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]", main_text):
    for n in expand(m.group(1)):
        if n not in order:
            order.append(n)
ref_lines = [l for l in refs.split("\n") if re.match(r"^\d+\. ", l)]
assert len(ref_lines) == 32, len(ref_lines)
old_refs = {int(l.split(".", 1)[0]): l.split(". ", 1)[1] for l in ref_lines}
missing = [n for n in old_refs if n not in order]
order += missing            # cited nowhere in the main text (should be none; kept at the end if any)
mapping = {old: new for new, old in enumerate(order, 1)}


def compress(nums):
    nums = sorted(set(nums))
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(str(nums[i]) if j - i < 2 else f"{nums[i]}–{nums[j]}")
        if j - i == 1:
            out[-1] = f"{nums[i]},{nums[j]}"
        i = j + 1
    return ",".join(out)


def remap(m):
    return "[" + compress([mapping[n] for n in expand(m.group(1))]) + "]"


head, tail = body.split("## References", 1)
head = re.sub(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]", remap, head)
new_ref_block = "\n".join(f"[{mapping[old]}] {old_refs[old]}" for old in sorted(old_refs, key=lambda o: mapping[o]))
tail_after_refs = tail.split("## Figure legends", 1)[1]
body = head + "## References\n\n" + new_ref_block + "\n\n## Figure legends" + tail_after_refs
uncited = [old for old in missing]

# ------------------------------------------------------------------ tables: renumber by first appearance; reorder blocks
main_text = body.split("## Tables")[0]
torder = []
for m in re.finditer(r"Table (\d)\b(?!\d)", main_text):
    if int(m.group(1)) not in torder:
        torder.append(int(m.group(1)))
for n in range(1, 6):
    if n not in torder:
        torder.append(n)
tmap = {old: new for new, old in enumerate(torder, 1)}
head, tail = body.split("## Tables", 1)
tables_block, supp_block = tail.split("## Supplementary information", 1)
head = re.sub(r"Table (\d)\b(?!\d)", lambda m: f"Table {tmap[int(m.group(1))]}", head)
blocks = re.split(r"(?=^\*\*Table \d \| )", tables_block.strip(), flags=re.M)
blocks = [b.strip() for b in blocks if b.strip()]
assert len(blocks) == 5, len(blocks)
by_old = {int(re.match(r"\*\*Table (\d)", b).group(1)): b for b in blocks}
new_blocks = []
for old in sorted(by_old, key=lambda o: tmap[o]):
    b = by_old[old]
    b = re.sub(r"Table (\d)\b(?!\d)", lambda m: f"Table {tmap[int(m.group(1))]}", b)   # one pass: caption and cross-references
    new_blocks.append(b)
supp_block = re.sub(r"Table (\d)\b(?!\d)", lambda m: f"Table {tmap[int(m.group(1))]}", supp_block)
body = head + "## Tables\n\n" + "\n\n".join(new_blocks) + "\n\n## Supplementary information" + supp_block

open(DST, "w", encoding="utf-8").write(body)
print("written", DST)
print("abstract words", nwords, "| significance words", sig_words)
print("reference mapping", mapping)
print("uncited references", uncited)
print("table mapping", tmap)
print("main-text words", len(re.sub(r"\|.*", "", body.split("## References")[0]).split()))
