# CMPB exemplars used to calibrate R6 (2026-10-27)

Five accepted CMPB papers were examined for structure and register; one in full (Hussain 2020), the others at abstract/highlights level.

| # | Paper | Type | What it does structurally | Borrowed into R6 |
|---|---|---|---|---|
| 1 | Hussain M et al. *Acquiring guideline-enabled data driven clinical knowledge model using formally verified refined knowledge acquisition method.* CMPB 2020;197:105701 | Formal verification of a CDSS knowledge-acquisition method (Z notation) | Background-and-Objective opens on the requirement ("validation and verification are the critical requirements…"); Methods names the method; Results give counts (nine criteria, four scenarios, 1,229 cases, 72.57 % vs 69.7 %, 47.8 % flawed paths); Conclusion claims generality of the method; 4 highlights, 52 refs | Cited as [33] (closest prior work); Results-paragraph density; generality sentence in Introduction and Discussion; highlight 5 on engine-agnostic tools |
| 2 | Thibeau-Sutre E et al. *ClinicaDL: an open-source deep learning software for reproducible neuroimaging processing.* CMPB 2022 | Open-source software/reproducibility paper | Abstract contains a "Software overview"; motivates with reproducibility and leakage checks; code availability is a first-class result | "Software availability" paragraph added to Declarations (language, dependencies, hardware, licence, Zenodo DOI plan) |
| 3 | Cabitza F et al. *The importance of being external. Methodological insights for the external validation of machine learning models in medicine.* CMPB 2021;208:106288 | Methodological insights | Argues external validation must be interpreted by cohort distance (meta-validation) | Cited as [34]; supports our reading of the heterogeneous external AUROCs as expected rather than as failure |
| 4 | MoCab (CMPB 2024, S0169260724003298) | Framework paper | Highlights stress open source; Results = demonstration on three model types | Pattern "framework + demonstration object" matches R6 (methods + Hemoglyph as object of study) |
| 5 | Zhang Y-F et al. HL7 RIM + ontology CDSS knowledge base. CMPB 2015 | Knowledge-base engineering | Formal data model first, evaluation second | Confirms Methods-first ordering (§2.2 knowledge base before §2.3–2.5 verification methods) |

Register observed across all five: numeric, Methods-first, no clinical-outcome claims, reproducibility and code release stated explicitly, modest conclusions, generality of the method asserted once. R6 was checked against each point.
