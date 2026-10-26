# B6 — Hemoglyph (labs + age/sex only) on the 50 PMC-Patients vignettes of Bhasuran et al. 2025 (npj Digit Med 2025;8:159)

Scoring key pre-specified in `scoring_key_prespecified.json` before any run (specific = the published final diagnosis; syndrome = the laboratory syndrome that contains it). Two arms, same engine, same key.

## Arm `parser` — end-to-end: free-text 'Lab Tests' paragraph -> Hemoglyph prose parser -> engine (no human in the loop)

cases 50; median analytes 5; cases with 0 analytes 1

## All 50 cases (n=50)

| level | top-1 | top-5 | top-10 |
|---|---|---|---|
| specific | 2% (0–10; 1/50) | 10% (4–21; 5/50) | 12% (6–24; 6/50) |
| syndrome | 28% (17–42; 14/50) | 44% (31–58; 22/50) | 46% (33–60; 23/50) |

## Lab-detectable final diagnoses (n=47)

| level | top-1 | top-5 | top-10 |
|---|---|---|---|
| specific | 2% (0–11; 1/47) | 11% (5–23; 5/47) | 13% (6–25; 6/47) |
| syndrome | 30% (19–44; 14/47) | 45% (31–59; 21/47) | 47% (33–61; 22/47) |

## Arm `manual` — author-structured panels (manual transcription of the same paragraph into analyte/value/unit, done before seeing engine output; narrative/symptoms never used)

cases 50; median analytes 11; cases with 0 analytes 2

## All 50 cases (n=50)

| level | top-1 | top-5 | top-10 |
|---|---|---|---|
| specific | 16% (8–29; 8/50) | 26% (16–40; 13/50) | 26% (16–40; 13/50) |
| syndrome | 40% (28–54; 20/50) | 68% (54–79; 34/50) | 70% (56–81; 35/50) |

## Lab-detectable final diagnoses (n=47)

| level | top-1 | top-5 | top-10 |
|---|---|---|---|
| specific | 17% (9–30; 8/47) | 28% (17–42; 13/47) | 28% (17–42; 13/47) |
| syndrome | 43% (30–57; 20/47) | 72% (58–83; 34/47) | 72% (58–83; 34/47) |

## Arm `manual_strict` — sensitivity: manual panels with every imputed / typo-corrected value removed (4 cases, 9 values; see 'imputed' in panel_overrides.json)

cases 50; median analytes 11; cases with 0 analytes 2

## All 50 cases (n=50)

| level | top-1 | top-5 | top-10 |
|---|---|---|---|
| specific | 16% (8–29; 8/50) | 24% (14–37; 12/50) | 24% (14–37; 12/50) |
| syndrome | 42% (29–56; 21/50) | 66% (52–78; 33/50) | 68% (54–79; 34/50) |

## Lab-detectable final diagnoses (n=47)

| level | top-1 | top-5 | top-10 |
|---|---|---|---|
| specific | 17% (9–30; 8/47) | 26% (15–40; 12/47) | 26% (15–40; 12/47) |
| syndrome | 45% (31–59; 21/47) | 70% (56–81; 33/47) | 70% (56–81; 33/47) |

Published comparators on the SAME 50 vignettes but with the FULL vignette (demographics + symptoms + narrative + labs), lenient scoring (Bhasuran et al. 2025, Table 2): GPT-4 top-1 60 %, top-5 81 %, top-10 83 %; GPT-3.5 / Claude-2 / Llama-2 / Mixtral lower; adding labs improved accuracy by up to 30 points. Hemoglyph here sees labs + age/sex only and no narrative — the comparison bounds the laboratory contribution, it is not head-to-head.

Per-case (manual arm; parser-arm ranks in brackets):

| pmid | final diagnosis | n obs | rank specific | rank syndrome | top-3 |
|---|---|---:|---|---|---|
| 24275336 | Acute cytomegalovirus hepatitis | 11 (5) | — (—) | 1 (1) | acute_hepatitis, hepatocellular_injury_pattern, autoimmune_hepatitis |
| 25733085 | Liver tuberculosis | 11 (5) | — (—) | 3 (—) | liver_cirrhosis, anemia, hepatocellular_injury_pattern |
| 26504769 | Type 2 diabetes, hypertension, benign prostate hypertrophy a | 8 (1) | 1 (—) | 1 (—) | type_2_diabetes, acute_kidney_injury, chronic_kidney_disease |
| 27572076 | Guillain-Barré Syndrome following acute hepatitis E | 12 (5) | 1 (—) | 1 (—) | hepatitis_e, hepatocellular_injury_pattern, isolated_hyperbilirubinemia_pattern |
| 28858213 | Liver failure due to exposure to a harmful algal bloom | 14 (1) | 1 (—) | 1 (—) | acute_liver_failure, hepatic_encephalopathy, autoimmune_hepatitis |
| 29049191 | Aspergillus fumigatus infection with liver failure | 11 (6) | — (—) | 1 (1) | hepatocellular_injury_pattern, isolated_hyperbilirubinemia_pattern, isoniazid_hepatotoxicity |
| 29594003 | Disseminated intravascular coagulopathy arising from systemi | 4 (3) | — (—) | — (—) |  |
| 31537508 | Vanishing bile duct syndrome (VBDS) and nodular sclerosis | 15 (11) | — (—) | 2 (3) | cholestasis, cholestatic_liver_injury_pattern, anemia |
| 32046690 | Type V hyperlipoproteinemia (HLP) | 4 (5) | 2 (—) | 2 (—) | anemia, hypertriglyceridemia, metabolic_syndrome |
| 33365209 | Ondansetron (OSDN)-induced hepatotoxicity | 11 (3) | — (—) | — (1) | nafl_d, metabolic_syndrome, ebola |
| 34689788 | Rhabdomyolysis (RM) and osteofascial compartment syndrome (O | 16 (16) | 1 (—) | 1 (8) | rhabdomyolysis, type_2_diabetes, mcardle_disease |
| 35223271 | Parvovirus b19-Induced Acute Hepatitis With Hepatosplenomega | 20 (16) | — (—) | 1 (1) | hepatocellular_injury_pattern, isolated_hyperbilirubinemia_pattern, acute_kidney_injury |
| 35387662 | Congenital bile acid synthesis disorder type 3 (CBAS3) | 0 (0) | — (—) | — (—) |  |
| 36537175 | Thallium intoxication | 17 (15) | — (—) | 6 (4) | liver_cirrhosis, thrombocytopenia, isolated_hyperbilirubinemia_pattern |
| 36941957 | Focal segmental glomerulosclerosis (FSGS) due to an MT-ND5 m | 4 (4) | — (—) | 2 (—) | hyperuricemia, chronic_kidney_disease, acute_kidney_injury |
| 36978171 | Idiosyncratic drug-induced liver injury related to use of RA | 13 (3) | — (—) | 1 (—) | hepatocellular_injury_pattern, isolated_hyperbilirubinemia_pattern, isoniazid_hepatotoxicity |
| 37026905 | Descending necrotizing mediastinitis (DNM) caused by Strepto | 6 (1) | — (—) | 1 (—) | sepsis, lactic_acidosis, bacterial_infection |
| 37631044 | Herb-Induced Liver Injury by Ayurvedic Ashwagandha | 16 (6) | — (—) | 1 (—) | hepatocellular_injury_pattern, isolated_hyperbilirubinemia_pattern, autoimmune_hepatitis |
| 24133669 | Autoimmune hepatitis (AIH) and Sjögren’s syndrome | 16 (5) | 1 (4) | 1 (1) | autoimmune_hepatitis, acute_hepatitis, isolated_hyperbilirubinemia_pattern |
| 35664380 | Chronic Kidney Disease of Unknown Origin (CKDu) | 15 (23) | 2 (6) | 1 (1) | acute_kidney_injury, chronic_kidney_disease, hyperuricemia |
| 30235756 | Drug-induced liver injury (DILI) caused by oseltamivir | 10 (3) | — (—) | — (—) | nafl_d, ebola, lassa_fever |
| 35974868 | Stage II classical Hodgkin lymphoma, nodular sclerosing subt | 15 (6) | — (—) | — (—) | cholestasis, isolated_hyperbilirubinemia_pattern, primary_biliary_cholangitis |
| 36397894 | Gallstone hepatitis | 15 (13) | — (—) | 2 (2) | acute_hepatitis, hepatocellular_injury_pattern, autoimmune_hepatitis |
| 36514699 | Intraperitoneal bladder rupture | 5 (1) | — (—) | 2 (—) | type_2_diabetes, acute_kidney_injury, chronic_kidney_disease |
| 36945289 | Selective Androgen Receptor Modulators (SARMs)-Induced Liver | 17 (5) | — (—) | — (—) | autoimmune_hepatitis, cholestasis, isolated_hyperbilirubinemia_pattern |
| 37025735 | Bile Cast Nephropathy due to Hepatitis A-induced Hyperbiliru | 13 (6) | 1 (—) | 1 (1) | hepatitis_a, hepatocellular_injury_pattern, acute_kidney_injury |
| 37435107 | Hyperbilirubinemia due to congenital hypopituitarism | 18 (14) | 1 (1) | 1 (1) | secondary_adrenal_insufficiency, central_adrenal_insufficiency, hypopituitarism_panhypopituitarism |
| 37519594 | Membranoproliferative glomerulonephritis (MPGN) associated w | 17 (10) | — (—) | 1 (1) | acute_kidney_injury, chronic_kidney_disease, sepsis |
| 37525805 | Acute Cholecystitis | 5 (4) | — (—) | — (—) | isolated_hyperbilirubinemia_pattern, nafl_d, metabolic_syndrome |
| 37546045 | Type V hyperlipoproteinemia | 10 (7) | 4 (3) | 4 (3) | nafl_d, type_2_diabetes, familial_chylomicronemia_syndrome |
| 19162360 | diabetic nephropathy with
near-nephrotic range proteinuria | 6 (4) | — (—) | 1 (1) | diabetes_mellitus, malnutrition, acute_glomerulonephritis |
| 31380008 | AMAN subtype of GBS | 31 (4) | — (—) | — (—) | hepatocellular_injury_pattern, cholestasis, hemochromatosis |
| 36307824 | Type D Lymphomatoid papulosis | 10 (3) | — (—) | — (—) | isolated_hyperbilirubinemia_pattern, viral_infection, nafl_d |
| 36407142 | Epstein-Barr virus (EBV) infection | 22 (20) | — (—) | 2 (—) | hereditary_hemochromatosis, acute_hepatitis, hepatocellular_injury_pattern |
| 36765433 | Severe acute respiratory coronavirus-2 infection, original w | 21 (1) | — (—) | — (—) | hyperuricemia, hypokalemia, hyponatremia |
| 37545787 | Caecal varices | 10 (7) | — (—) | 3 (3) | acute_kidney_injury, chronic_kidney_disease, anemia |
| 19592143 | Diabetic Neuropathy | 4 (2) | — (—) | 3 (3) | acute_kidney_injury, chronic_kidney_disease, diabetes_mellitus |
| 23415437 | Coronary heart disease (CHD) caused by ApoA-INashua mutation | 19 (18) | — (—) | — (—) | metabolic_syndrome, hyperinsulinemic_hypoglycemia, prediabetes |
| 23569786 | Hyperglyceridemia | 6 (4) | 3 (2) | 3 (2) | metabolic_syndrome, diabetes_mellitus, hypertriglyceridemia |
| 23975921 | Stage IV classical Hodgkin's lymphoma | 10 (6) | — (—) | — (—) | hepatocellular_injury_pattern, cholestasis, epstein_barr_vca_igg_antibody_seropositivity |
| 29033779 | Nafcillin-induced acute liver injury | 12 (3) | — (—) | — (—) | cholestasis, liver_cirrhosis, isolated_hyperbilirubinemia_pattern |
| 30186097 | Idiosyncratic drug-induced liver injury from ingestion of gi | 13 (5) | — (—) | 1 (—) | hepatocellular_injury_pattern, cholestasis, isolated_hyperbilirubinemia_pattern |
| 31497118 | Drug-induce liver injury (DILI) from levetiracetam (LEV) to  | 0 (3) | — (—) | — (1) |  |
| 31497445 | Vancomycin-induced DRESS syndrome | 12 (7) | — (—) | 3 (1) | acute_cholangitis, ascending_cholangitis, acute_kidney_injury |
| 32864246 | Elevated low-density lipoprotein cholesterol (LDL-C) due to  | 5 (5) | 2 (2) | 1 (1) | hyperlipidemia, hypercholesterolemia, hypothyroidism |
| 33763324 | Glycogen hepatopathy (GH) | 4 (3) | — (—) | 1 (1) | hepatocellular_injury_pattern, diabetes_mellitus, alcoholic_liver_disease |
| 34692794 | Homozygous forms of familial hypercholesterolemia (HoFH) | 8 (4) | 1 (—) | 1 (—) | familial_hypercholesterolemia, elevated_lpa_pattern, hypercholesterolemia |
| 36060394 | Acute Myeloid Leukemia Masquerading as Decompensated Cirrhos | 9 (9) | — (—) | 3 (3) | acute_kidney_injury, hepatocellular_injury_pattern, thrombocytopenia |
| 35844332 | Elevated International Normalized Ratio Due to Apixaban | 7 (1) | — (—) | — (—) | malnutrition, liver_cirrhosis |
| 26962840 | Isospora belli infection | 8 (1) | — (—) | 4 (—) | hyper_ige_syndrome, hepatocellular_injury_pattern, strongyloidiasis |
