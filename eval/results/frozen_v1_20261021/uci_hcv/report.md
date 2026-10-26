# UCI HCV dataset (Hoffmann 2018) — held-out real-patient evaluation

n = 615 (donors 533, suspect donors 7, hepatitis 24, fibrosis 21, cirrhosis 30). Engine not modified after running on this data. Inputs in native SI units (conversion exercised).

## Task A — any liver disease vs blood donors

- AUROC = **0.891** (bootstrap 95% CI 0.842–0.934); positives 75, negatives 533
- threshold 0.5: sensitivity 25.3% (16.9–36.2), specificity 97.7% (96.1–98.7)
- threshold 0.7: sensitivity 10.7% (5.5–19.7), specificity 100.0% (99.3–100.0)

## Task B — cirrhosis vs all non-cirrhotic subjects

- AUROC = **0.948** (bootstrap 95% CI 0.889–0.986); positives 30, negatives 578
- threshold 0.5: sensitivity 56.7% (39.2–72.6), specificity 100.0% (99.3–100.0)
- threshold 0.7: sensitivity 13.3% (5.3–29.7), specificity 100.0% (99.3–100.0)

## Task A' — hepatitis only vs donors

- AUROC = **0.789** (bootstrap 95% CI 0.655–0.899); positives 24, negatives 533
- threshold 0.5: sensitivity 4.2% (0.7–20.2), specificity 97.7% (96.1–98.7)
- threshold 0.7: sensitivity 4.2% (0.7–20.2), specificity 100.0% (99.3–100.0)

## Task A'' — fibrosis only vs donors

- AUROC = **0.912** (bootstrap 95% CI 0.874–0.946); positives 21, negatives 533
- threshold 0.5: sensitivity 0.0% (0.0–15.5), specificity 97.7% (96.1–98.7)
- threshold 0.7: sensitivity 0.0% (0.0–15.5), specificity 100.0% (99.3–100.0)

## Task A''' — cirrhosis vs donors

- AUROC = **0.959** (bootstrap 95% CI 0.932–0.982); positives 30, negatives 533
- threshold 0.5: sensitivity 60.0% (42.3–75.4), specificity 97.7% (96.1–98.7)
- threshold 0.7: sensitivity 23.3% (11.8–40.9), specificity 100.0% (99.3–100.0)

## Per-class sensitivity of the liver score (threshold 0.5)

| class | n | liver score ≥ 0.5 | cirrhosis score ≥ 0.5 | most frequent top-1 |
|---|---:|---|---|---|
| blood donor | 533 | 2.3% (1.3–3.9) | 0.0% (0.0–0.7) | hypercholesterolemia (279), hemolytic_anemia (152), cholestasis (24) |
| suspect donor | 7 | 71.4% (35.9–91.8) | 28.6% (8.2–64.1) | liver_cirrhosis (2), acute_kidney_injury (1), cholestasis (1) |
| hepatitis | 24 | 4.2% (0.7–20.2) | 0.0% (0.0–13.8) | hypercholesterolemia (10), alcoholic_liver_disease (7), nafl_d (2) |
| fibrosis | 21 | 0.0% (0.0–15.5) | 0.0% (0.0–15.5) | nafl_d (8), alcoholic_liver_disease (7), hypercholesterolemia (2) |
| cirrhosis | 30 | 60.0% (42.3–75.4) | 56.7% (39.2–72.6) | liver_cirrhosis (12), alcoholic_hepatitis_pattern (4), nafl_d (3) |

Latency median 362 ms, p95 820 ms.

## False-positive donors (liver score ≥ 0.5): 12

- donor 90: [('cholestasis', 0.514), ('primary_biliary_cholangitis', 0.49), ('hypercholesterolemia', 0.488)]
- donor 142: [('cholestasis', 0.514), ('primary_biliary_cholangitis', 0.49), ('hypercholesterolemia', 0.488)]
- donor 147: [('cholestasis', 0.514), ('hyperlipidemia', 0.49), ('primary_biliary_cholangitis', 0.49)]
- donor 206: [('cholestasis', 0.528), ('hypercholesterolemia', 0.501), ('primary_biliary_cholangitis', 0.49)]
- donor 216: [('cholestasis', 0.514), ('primary_biliary_cholangitis', 0.49), ('hypercholesterolemia', 0.488)]
- donor 228: [('cholestasis', 0.544), ('primary_biliary_cholangitis', 0.49), ('nafl_d', 0.387)]
- donor 242: [('cholestasis', 0.544), ('hypercholesterolemia', 0.517), ('primary_biliary_cholangitis', 0.49)]
- donor 290: [('cholestasis', 0.514), ('primary_biliary_cholangitis', 0.49), ('hypercholesterolemia', 0.488)]
- donor 419: [('cholestasis', 0.514), ('primary_biliary_cholangitis', 0.49), ('hypercholesterolemia', 0.488)]
- donor 459: [('cholestasis', 0.514), ('hyperlipidemia', 0.49), ('primary_biliary_cholangitis', 0.49)]
- donor 463: [('cholestasis', 0.544), ('hypercholesterolemia', 0.517), ('primary_biliary_cholangitis', 0.49)]
- donor 482: [('cholestasis', 0.514), ('primary_biliary_cholangitis', 0.49), ('hypercholesterolemia', 0.488)]

## Missed liver-disease subjects (liver score < 0.5)

- 1=Hepatitis #541: [('hypercholesterolemia', 0.576), ('hemolytic_anemia', 0.116)]
- 1=Hepatitis #542: [('nafl_d', 0.61), ('cholestasis', 0.282), ('ebola', 0.162)]
- 1=Hepatitis #543: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.352)]
- 1=Hepatitis #544: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.321)]
- 1=Hepatitis #545: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('hemolytic_anemia', 0.116)]
- 1=Hepatitis #546: [('nafl_d', 0.348), ('co_elevated_alanine_aminotransferase_with_elevated_total_protein', 0.288), ('metabolic_syndrome', 0.202)]
- 1=Hepatitis #547: [('hypercholesterolemia', 0.576), ('nafl_d', 0.433), ('metabolic_syndrome', 0.207)]
- 1=Hepatitis #548: [('hypercholesterolemia', 0.576), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 1=Hepatitis #549: [('hypercholesterolemia', 0.576), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 1=Hepatitis #550: [('hypercholesterolemia', 0.576), ('hemolytic_anemia', 0.116)]
- 1=Hepatitis #551: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.352)]
- 1=Hepatitis #552: [('hypercholesterolemia', 0.576), ('hemolytic_anemia', 0.117)]
- 1=Hepatitis #553: [('isolated_hyperbilirubinemia_pattern', 0.592), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 1=Hepatitis #554: [('hypercholesterolemia', 0.645), ('isolated_hyperbilirubinemia_pattern', 0.592), ('alcoholic_liver_disease', 0.49)]
- 1=Hepatitis #555: [('hemolytic_anemia', 0.117), ('liver_cirrhosis', 0.109), ('cholestasis', 0.089)]
- 1=Hepatitis #556: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('cholestasis', 0.279)]
- 1=Hepatitis #557: [('hypercholesterolemia', 0.576), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 1=Hepatitis #558: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.352)]
- 1=Hepatitis #560: [('acute_kidney_injury', 0.54), ('hypercholesterolemia', 0.513), ('alcoholic_liver_disease', 0.49)]
- 1=Hepatitis #561: [('hypercholesterolemia', 0.576), ('hemolytic_anemia', 0.116)]
- 1=Hepatitis #562: [('hypercholesterolemia', 0.576), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 1=Hepatitis #563: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.147)]
- 1=Hepatitis #564: [('isolated_hyperbilirubinemia_pattern', 0.592), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 2=Fibrosis #565: [('hypercholesterolemia', 0.576), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 2=Fibrosis #566: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.352)]
- 2=Fibrosis #567: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.352)]
- 2=Fibrosis #568: [('isolated_hyperbilirubinemia_pattern', 0.592), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 2=Fibrosis #569: [('nafl_d', 0.514), ('metabolic_syndrome', 0.306), ('cholestasis', 0.278)]
- 2=Fibrosis #570: [('nafl_d', 0.511), ('metabolic_syndrome', 0.306), ('cholestasis', 0.288)]
- 2=Fibrosis #571: [('nafl_d', 0.514), ('isoniazid_hepatotoxicity', 0.342), ('co_elevated_alanine_aminotransferase_with_elevated_total_protein', 0.312)]
- 2=Fibrosis #572: [('nafl_d', 0.422), ('cholestasis', 0.258), ('liver_cirrhosis', 0.155)]
- 2=Fibrosis #573: [('isolated_hyperbilirubinemia_pattern', 0.592), ('hypercholesterolemia', 0.576), ('alcoholic_liver_disease', 0.49)]
- 2=Fibrosis #574: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.352)]
- 2=Fibrosis #575: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.352)]
- 2=Fibrosis #576: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.147)]
- 2=Fibrosis #577: [('nafl_d', 0.521), ('metabolic_syndrome', 0.306), ('cholestasis', 0.289)]
- 2=Fibrosis #578: [('nafl_d', 0.687), ('alcoholic_liver_disease', 0.49), ('autoimmune_hepatitis', 0.49)]
- 2=Fibrosis #579: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.323)]
- 2=Fibrosis #580: [('hypercholesterolemia', 0.576), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 2=Fibrosis #581: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.169)]
- 2=Fibrosis #582: [('hemochromatosis', 0.258), ('nafl_d', 0.162), ('cholestasis', 0.138)]
- 2=Fibrosis #583: [('nafl_d', 0.455), ('metabolic_syndrome', 0.306), ('cholestasis', 0.176)]
- 2=Fibrosis #584: [('cholestasis', 0.249), ('hemochromatosis', 0.241), ('nafl_d', 0.162)]
- 2=Fibrosis #585: [('nafl_d', 0.506), ('metabolic_syndrome', 0.306), ('cholestasis', 0.288)]
- 3=Cirrhosis #586: [('nafl_d', 0.61), ('cholestasis', 0.282), ('metabolic_syndrome', 0.224)]
- 3=Cirrhosis #589: [('isolated_hyperbilirubinemia_pattern', 0.592), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 3=Cirrhosis #592: [('acute_kidney_injury', 0.6), ('cholestasis', 0.279), ('chronic_kidney_disease', 0.24)]
- 3=Cirrhosis #593: [('hypercholesterolemia', 0.576), ('nafl_d', 0.514), ('metabolic_syndrome', 0.306)]
- 3=Cirrhosis #594: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.362)]
- 3=Cirrhosis #600: [('isolated_hyperbilirubinemia_pattern', 0.592), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 3=Cirrhosis #603: [('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488), ('nafl_d', 0.362)]
- 3=Cirrhosis #604: [('nafl_d', 0.443), ('liver_cirrhosis', 0.274), ('cholestasis', 0.256)]
- 3=Cirrhosis #608: [('acute_kidney_injury', 0.56), ('isolated_hyperbilirubinemia_pattern', 0.532), ('chronic_kidney_disease', 0.308)]
- 3=Cirrhosis #610: [('acute_kidney_injury', 0.513), ('alcoholic_liver_disease', 0.49), ('liver_cirrhosis', 0.488)]
- 3=Cirrhosis #614: [('nafl_d', 0.444), ('liver_cirrhosis', 0.427), ('malnutrition', 0.287)]
- 3=Cirrhosis #615: [('hypercholesterolemia', 0.576), ('nafl_d', 0.382), ('metabolic_syndrome', 0.306)]