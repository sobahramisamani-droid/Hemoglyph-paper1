# Cover letter — Journal of Biomedical Informatics

Dear Editors,

Please consider the enclosed original methodological article, "A verifiable, auditable, locally run rule engine for laboratory-panel interpretation: architecture, property-based verification, source-concordance audit, pre-specified retrospective evaluation and blinded comparison with an unnamed frontier LLM", for publication in the Journal of Biomedical Informatics.

**Why JBI.** The contribution is methodological rather than clinical: we describe how a knowledge-based system whose 33,000 rules were drafted with AI assistance can be made *verifiable* (executable invariants run on every release), *auditable* (every ranked output traces to a rule identifier and source) and *honestly evaluated* (frozen protocol, one-shot quarantine on >20,000 encounters, a failed first quarantine round reported, and a blinded comparison with a frontier LLM). We also report a pre-specified (internally frozen, not publicly registered) source-concordance audit whose result is unfavourable to our own system—92 % of sampled rules could not be verified from their locators and at least 7.5 % were demonstrably discordant—and we draw the methodological conclusion that provenance granularity, not rule count, is the binding constraint on auditability of AI-drafted knowledge bases.

**What is new.** (i) Property-based verification for a clinical rule engine, which found a ranking defect that 353 adversarial vignettes had missed; (ii) a reproducible source-concordance audit protocol with two denominators and explicit selection-bias caveats; (iii) a comparison in which a deterministic, untrained engine reaches recall@5 parity with an unnamed frontier LLM on ICU panels while remaining fully traceable.

**Healthcare-professional involvement (JBI scope statement).** The Guide for Authors expects involvement of healthcare professionals in motivating the work and evaluating results. We state plainly where we stand: no clinician is an author, no clinician audited the rule base, and no clinician adjudicated outputs. The clinical motivation is drawn from the laboratory-medicine literature on post-analytical error and interpretive commenting, which we cite, and the reference standards are clinician-documented problem lists (eICU) and guideline-defined criteria (NHANES). The source-concordance audit was performed by a single declared rater (an AI agent under a frozen protocol); a second human non-clinician rater returned templated verdicts in a first round and that round was rejected and reported rather than averaged in. A clinician-in-the-loop reader study is planned as a separate paper and is explicitly outside the present one. If the editors consider that this absence places the manuscript out of scope, we would value being told so at triage rather than after review.

**Formatting.** Structured abstract (297 words), five highlights (≤ 85 characters), seven keywords, Statement of Significance at the end of the Introduction, numbered sections, CRediT statement, declaration of generative-AI use, ethics statement with the exemption rationale, data statement, and a graphical abstract (3900 × 1950 px PNG and PDF) are supplied.

**Declarations.** The first author is a secondary-school student (Allameh Helli 10, NODET, Tehran); the registries were AI-drafted and not expert-curated, which the manuscript states throughout. The system is a research prototype and no clinical or regulatory claim is made. Code (AGPL-3.0) and registry (CC BY-SA 4.0) are public. No funding was received; the authors cannot pay an article-processing charge and request the subscription publication route. The work is not under consideration elsewhere; a preprint may be deposited on medRxiv.

Suggested reviewers (no conflicts; none has collaborated with the authors):
1. Prof. Dean F. Sittig, UTHealth Houston — CDS safety and evaluation.
2. Prof. Adam Wright, Vanderbilt University Medical Center — CDS rule malfunction and knowledge-base maintenance.
3. Prof. Mor Peleg, University of Haifa — computer-interpretable guidelines (former JBI editor; suggest only if eligible).
4. Dr. Christopher McCudden, University of Ottawa / The Ottawa Hospital — laboratory-medicine decision support and verification.
5. Prof. Ferdinand Dhombres, Sorbonne Université — knowledge representation in clinical informatics.

Sincerely,
Sobhan Bahrami (corresponding author; ORCID 0009-0004-6639-5081), on behalf of all authors
