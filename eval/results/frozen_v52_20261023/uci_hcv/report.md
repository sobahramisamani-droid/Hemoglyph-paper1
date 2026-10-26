# UCI HCV dataset (Hoffmann 2018) — held-out real-patient evaluation

n = 615 (donors 533, suspect donors 7, hepatitis 24, fibrosis 21, cirrhosis 30). Engine not modified after running on this data. Inputs in native SI units (conversion exercised).

## Task A — any liver disease vs blood donors

- AUROC = **0.925** (bootstrap 95% CI 0.881–0.962); positives 75, negatives 533
- threshold 0.5: sensitivity 29.3% (20.2–40.4), specificity 100.0% (99.3–100.0)
- threshold 0.7: sensitivity 14.7% (8.4–24.4), specificity 100.0% (99.3–100.0)

## Task B — cirrhosis vs all non-cirrhotic subjects

- AUROC = **0.909** (bootstrap 95% CI 0.837–0.969); positives 30, negatives 578
- threshold 0.5: sensitivity 53.3% (36.1–69.8), specificity 100.0% (99.3–100.0)
- threshold 0.7: sensitivity 10.0% (3.5–25.6), specificity 100.0% (99.3–100.0)

## Task A' — hepatitis only vs donors

- AUROC = **0.823** (bootstrap 95% CI 0.703–0.923); positives 24, negatives 533
- threshold 0.5: sensitivity 4.2% (0.7–20.2), specificity 100.0% (99.3–100.0)
- threshold 0.7: sensitivity 4.2% (0.7–20.2), specificity 100.0% (99.3–100.0)

## Task A'' — fibrosis only vs donors

- AUROC = **0.976** (bootstrap 95% CI 0.958–0.990); positives 21, negatives 533
- threshold 0.5: sensitivity 4.8% (0.8–22.7), specificity 100.0% (99.3–100.0)
- threshold 0.7: sensitivity 4.8% (0.8–22.7), specificity 100.0% (99.3–100.0)

## Task A''' — cirrhosis vs donors

- AUROC = **0.970** (bootstrap 95% CI 0.926–0.995); positives 30, negatives 533
- threshold 0.5: sensitivity 66.7% (48.8–80.8), specificity 100.0% (99.3–100.0)
- threshold 0.7: sensitivity 30.0% (16.7–47.9), specificity 100.0% (99.3–100.0)

## Per-class sensitivity of the liver score (threshold 0.5)

| class | n | liver score ≥ 0.5 | cirrhosis score ≥ 0.5 | most frequent top-1 |
|---|---:|---|---|---|
| blood donor | 533 | 0.0% (0.0–0.7) | 0.0% (0.0–0.7) | hypercholesterolemia (299), hemolytic_anemia (161), nafl_d (18) |
| suspect donor | 7 | 71.4% (35.9–91.8) | 28.6% (8.2–64.1) | liver_cirrhosis (4), chronic_kidney_disease (1), hepatocellular_injury_pattern (1) |
| hepatitis | 24 | 4.2% (0.7–20.2) | 0.0% (0.0–13.8) | hypercholesterolemia (10), alcoholic_liver_disease (7), nafl_d (2) |
| fibrosis | 21 | 4.8% (0.8–22.7) | 0.0% (0.0–15.5) | alcoholic_liver_disease (7), nafl_d (7), hypercholesterolemia (3) |
| cirrhosis | 30 | 66.7% (48.8–80.8) | 53.3% (36.1–69.8) | liver_cirrhosis (10), alcoholic_hepatitis_pattern (4), nafl_d (3) |

Latency median 412 ms, p95 766 ms.

## False-positive donors (liver score ≥ 0.5): 0


## Missed liver-disease subjects (liver score < 0.5)

- 1=Hepatitis #541: [('hypercholesterolemia', 0.576), ('hemolytic_anemia', 0.116)]
- 1=Hepatitis #542: [('nafl_d', 0.61), ('cholestasis', 0.282), ('ebola', 0.162)]
- 1=Hepatitis #543: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('cholestasis', 0.151)]
- 1=Hepatitis #544: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('metabolic_syndrome', 0.207)]
- 1=Hepatitis #545: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('hemolytic_anemia', 0.116)]
- 1=Hepatitis #546: [('nafl_d', 0.348), ('metabolic_syndrome', 0.202), ('hemolytic_anemia', 0.117)]
- 1=Hepatitis #547: [('hypercholesterolemia', 0.576), ('nafl_d', 0.433), ('metabolic_syndrome', 0.207)]
- 1=Hepatitis #548: [('hypercholesterolemia', 0.576), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 1=Hepatitis #549: [('hypercholesterolemia', 0.576), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 1=Hepatitis #550: [('hypercholesterolemia', 0.576), ('hemolytic_anemia', 0.116)]
- 1=Hepatitis #551: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('cholestasis', 0.138)]
- 1=Hepatitis #552: [('hypercholesterolemia', 0.576), ('hemolytic_anemia', 0.117)]
- 1=Hepatitis #553: [('isolated_hyperbilirubinemia_pattern', 0.592), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 1=Hepatitis #554: [('hypercholesterolemia', 0.645), ('isolated_hyperbilirubinemia_pattern', 0.592), ('alcoholic_liver_disease', 0.49)]
- 1=Hepatitis #555: [('hemolytic_anemia', 0.117)]
- 1=Hepatitis #556: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('cholestasis', 0.138)]
- 1=Hepatitis #557: [('hypercholesterolemia', 0.576), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 1=Hepatitis #558: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('hypercholesterolemia', 0.2)]
- 1=Hepatitis #560: [('acute_kidney_injury', 0.54), ('hypercholesterolemia', 0.513), ('alcoholic_liver_disease', 0.49)]
- 1=Hepatitis #561: [('hypercholesterolemia', 0.576), ('hemolytic_anemia', 0.116)]
- 1=Hepatitis #562: [('hypercholesterolemia', 0.576), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 1=Hepatitis #563: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('hemolytic_anemia', 0.116)]
- 1=Hepatitis #564: [('isolated_hyperbilirubinemia_pattern', 0.592), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 2=Fibrosis #565: [('hypercholesterolemia', 0.576), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 2=Fibrosis #566: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('cholestasis', 0.138)]
- 2=Fibrosis #567: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('cholestasis', 0.151)]
- 2=Fibrosis #568: [('isolated_hyperbilirubinemia_pattern', 0.592), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 2=Fibrosis #569: [('nafl_d', 0.514), ('metabolic_syndrome', 0.306), ('cholestasis', 0.278)]
- 2=Fibrosis #570: [('nafl_d', 0.511), ('metabolic_syndrome', 0.306), ('cholestasis', 0.288)]
- 2=Fibrosis #572: [('nafl_d', 0.444), ('cholestasis', 0.258), ('hemolytic_anemia', 0.117)]
- 2=Fibrosis #573: [('hypercholesterolemia', 0.576), ('isolated_hyperbilirubinemia_pattern', 0.592), ('alcoholic_liver_disease', 0.49)]
- 2=Fibrosis #574: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('cholestasis', 0.143)]
- 2=Fibrosis #575: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('cholestasis', 0.138)]
- 2=Fibrosis #576: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('hemolytic_anemia', 0.117)]
- 2=Fibrosis #577: [('nafl_d', 0.521), ('metabolic_syndrome', 0.306), ('cholestasis', 0.289)]
- 2=Fibrosis #578: [('nafl_d', 0.533), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 2=Fibrosis #579: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('cholestasis', 0.138)]
- 2=Fibrosis #580: [('hypercholesterolemia', 0.576), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 2=Fibrosis #581: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('hemolytic_anemia', 0.117)]
- 2=Fibrosis #582: [('hemochromatosis', 0.258), ('nafl_d', 0.162), ('cholestasis', 0.138)]
- 2=Fibrosis #583: [('nafl_d', 0.455), ('metabolic_syndrome', 0.306), ('cholestasis', 0.176)]
- 2=Fibrosis #584: [('cholestasis', 0.249), ('hemochromatosis', 0.241), ('nafl_d', 0.162)]
- 2=Fibrosis #585: [('nafl_d', 0.506), ('metabolic_syndrome', 0.306), ('cholestasis', 0.288)]
- 3=Cirrhosis #586: [('nafl_d', 0.61), ('cholestasis', 0.282), ('metabolic_syndrome', 0.224)]
- 3=Cirrhosis #592: [('acute_kidney_injury', 0.831), ('chronic_kidney_disease', 0.72), ('gout', 0.172)]
- 3=Cirrhosis #593: [('hypercholesterolemia', 0.576), ('nafl_d', 0.514), ('metabolic_syndrome', 0.306)]
- 3=Cirrhosis #594: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('cholestasis', 0.175)]
- 3=Cirrhosis #600: [('isolated_hyperbilirubinemia_pattern', 0.592), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 3=Cirrhosis #603: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('cholestasis', 0.175)]
- 3=Cirrhosis #604: [('nafl_d', 0.472), ('liver_cirrhosis', 0.274), ('cholestasis', 0.256)]
- 3=Cirrhosis #608: [('chronic_kidney_disease', 0.7), ('acute_kidney_injury', 0.56), ('isolated_hyperbilirubinemia_pattern', 0.592)]
- 3=Cirrhosis #614: [('nafl_d', 0.444), ('liver_cirrhosis', 0.427), ('malnutrition', 0.287)]
- 3=Cirrhosis #615: [('hypercholesterolemia', 0.576), ('nafl_d', 0.382), ('metabolic_syndrome', 0.306)]