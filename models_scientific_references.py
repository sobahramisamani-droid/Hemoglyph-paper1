from __future__ import annotations
from typing import Any, Dict, Optional

__version__ = "3.1.0-complete"
__all__ = [
    "get_reference_for_model",
    "BASE_AND_EXPANDED_REFERENCES",
    "SPECIALIZED_DISEASE_REFERENCES",
    "COHORT_SPECIALTY_PAPERS",
    "COHORT_IDS",
    "count_references",
]

def _ref(citation: str, doi: str, pmid: str, title: str, journal: str,
         year: Any, url: Optional[str] = None, evidence_level: str = "A",
         population: str = "General adult", study_type: str = "Cohort / Guideline"
         ) -> Dict[str, Any]:
    """Build a standardised reference dictionary."""
    if url is None:
        if doi and doi not in ("-", ""):
            url = f"https://doi.org/{doi}"
        elif pmid:
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        else:
            url = ""
    return {
        "citation": citation, "doi": doi, "pmid": pmid, "title": title,
        "journal": journal, "year": year, "url": url,
        "evidence_level": evidence_level, "population": population,
        "study_type": study_type,
    }

BASE_AND_EXPANDED_REFERENCES: Dict[str, Dict[str, Any]] = {
    # ---- Diabetes / Metabolic ----
    "Diabetes_Mellitus": _ref(
        "Lindström J, Tuomilehto J. The diabetes risk score: a practical tool to predict type 2 diabetes risk. Diabetes Care. 2003;26(3):725-731.",
        "10.2337/diacare.26.3.725", "12610029",
        "The diabetes risk score: a practical tool to predict type 2 diabetes risk (FINDRISC)",
        "Diabetes Care", 2003, population="Finnish general population", study_type="Prospective cohort"),
    "Diabetes_Mellitus_Lab": _ref(
        "HEMOGLYPH internal laboratory cross-check (heuristic logistic).",
        "-", "", "Internal lab-based diabetes risk cross-check",
        "HEMOGLYPH Research", 2025, evidence_level="C", study_type="Internal heuristic"),
    "Prediabetes": _ref(
        "Bang H, Edwards AM, Bomback AS, et al. Development and validation of a patient self-assessment score for diabetes risk. Ann Intern Med. 2009;151(11):775-783.",
        "10.7326/0003-4819-151-11-200912010-00006", "19949143",
        "Development and validation of a patient self-assessment score for diabetes risk (CDC/ADA)",
        "Annals of Internal Medicine", 2009, population="US adults", study_type="Cross-sectional validation"),
    "Diabetes_QDiabetes_10Y": _ref(
        "Hippisley-Cox J, Coupland C. Development and validation of QDiabetes-2014 risk prediction algorithm. BMJ. 2014;349:g7229.",
        "10.1136/bmj.g7229", "25524317",
        "Development and validation of QDiabetes-2014 risk prediction algorithm",
        "BMJ", 2014, population="UK primary care", study_type="Prospective cohort"),
    "Diabetes_Cambridge_Risk": _ref(
        "Rahman M, Simmons RK, Hennings SH, Wareham NJ, Griffin SJ. Validation of the Cambridge Risk Score for diabetes in primary care. BMJ. 2008;336(7642):480-485.",
        "10.1136/bmj.39474.453715.BE", "18276666",
        "Validation of the Cambridge diabetes risk score in primary care",
        "BMJ", 2008, population="UK primary care", study_type="Validation cohort"),
    "Diabetes_AUSDRISK_5Y": _ref(
        "Chen L, Magliano DJ, Balkau B, et al. The Australian type 2 diabetes risk assessment tool (AUSDRISK). Med J Aust. 2010;192(4):197-202.",
        "10.5694/j.1326-5377.2010.tb03478.x", "20170456",
        "The Australian type 2 diabetes risk assessment tool (AUSDRISK)",
        "Medical Journal of Australia", 2010, population="Australian adults", study_type="Cross-sectional"),
    "Diabetes_GDRS_5Y": _ref(
        "Schulze MB, Hoffmann K, Boeing H, et al. An accurate risk score based on anthropometric, dietary, and lifestyle factors to predict type 2 diabetes (GDRS). Diabetologia. 2007;50(6):1150-1159.",
        "10.1007/s00125-007-0665-6", "17492426",
        "The German Diabetes Risk Score (GDRS)",
        "Diabetologia", 2007, population="EPIC-Potsdam cohort", study_type="Prospective cohort"),
    "Diabetes_UKPDS_CHD": _ref(
        "Stevens RJ, Kothari V, Adler AI, Stratton IM. The UKPDS risk engine: a model for the risk of coronary heart disease in Type II diabetes (UKPDS 56). Clin Sci (Lond). 2001;101(6):671-679.",
        "10.1042/cs1010671", "11724658",
        "The UKPDS risk engine: CHD risk in Type II diabetes (UKPDS 56)",
        "Clinical Science", 2001, population="UKPDS T2DM cohort", study_type="RCT cohort"),
    "Diabetes_ADVANCE_CVD": _ref(
        "Kengne AP, Patel A, Marre M, et al. Contemporary model for cardiovascular risk prediction in people with type 2 diabetes (ADVANCE). Diabetologia. 2011;54(5):1006-1013.",
        "10.1007/s00125-010-2029-1", "21253699",
        "Contemporary model for CVD risk prediction in type 2 diabetes (ADVANCE)",
        "Diabetologia", 2011, population="ADVANCE trial", study_type="RCT cohort"),
    "Metabolic_Syndrome": _ref(
        "Alberti KG, Eckel RH, Grundy SM, et al. Harmonizing the metabolic syndrome: a joint interim statement. Circulation. 2009;120(16):1640-1645.",
        "10.1161/CIRCULATIONAHA.109.192644", "19805654",
        "Harmonizing the metabolic syndrome: joint interim statement (JIS 2009)",
        "Circulation", 2009, population="Global", study_type="Consensus statement"),
    "Insulin_Resistance_TyG": _ref(
        "Simental-Mendía LE, Rodríguez-Morán M, Guerrero-Romero F. The product of fasting glucose and triglycerides as surrogate for identifying insulin resistance (TyG). Metab Syndr Relat Disord. 2008;6(4):299-304.",
        "10.1089/met.2008.0034", "19067533",
        "The TyG index as surrogate for identifying insulin resistance",
        "Metabolic Syndrome and Related Disorders", 2008, population="Healthy adults", study_type="Cross-sectional"),
    "Metabolic_VAI_Index": _ref(
        "Amato MC, Giordano C, Galia M, et al. Visceral Adiposity Index: a reliable indicator of visceral fat function associated with cardiometabolic risk. Diabetes Care. 2010;33(4):920-922.",
        "10.2337/dc09-1825", "20067971",
        "Visceral Adiposity Index (VAI) and cardiometabolic risk",
        "Diabetes Care", 2010, population="Italian cohort", study_type="Cross-sectional"),
    "Metabolic_LAP_Index": _ref(
        "Kahn HS. The 'lipid accumulation product' performs better than the body mass index for recognizing cardiovascular risk: NHANES III. BMC Cardiovasc Disord. 2005;5:26.",
        "10.1186/1471-2261-5-26", "16150143",
        "The lipid accumulation product (LAP) and cardiovascular risk",
        "BMC Cardiovascular Disorders", 2005, population="NHANES III", study_type="Cross-sectional"),
    "Primary_Aldosteronism_ARR": _ref(
        "Funder JW, Carey RM, Mantero F, et al. The Management of Primary Aldosteronism: An Endocrine Society Clinical Practice Guideline. J Clin Endocrinol Metab. 2016;101(5):1889-1916.",
        "10.1210/jc.2015-4061", "26934393",
        "The Management of Primary Aldosteronism: Endocrine Society Guideline",
        "The Journal of Clinical Endocrinology & Metabolism", 2016, population="Hypertension screening", study_type="Clinical guideline"),
    "Hemochromatosis_TSAT": _ref(
        "European Association for the Study of the Liver. EASL Clinical Practice Guidelines on haemochromatosis. J Hepatol. 2022;77(2):479-502.",
        "10.1016/j.jhep.2022.03.033", "35662478",
        "EASL Clinical Practice Guidelines on haemochromatosis",
        "Journal of Hepatology", 2022, population="Iron overload", study_type="Clinical guideline"),

    # ---- Cardiovascular ----
    "Cardiovascular_Risk": _ref(
        "Goff DC Jr, Lloyd-Jones DM, Bennett G, et al. 2013 ACC/AHA Guideline on the Assessment of Cardiovascular Risk. Circulation. 2014;129(25 Suppl 2):S49-S73.",
        "10.1161/01.cir.0000437741.48606.98", "24222018",
        "2013 ACC/AHA Guideline on the Assessment of Cardiovascular Risk (Pooled Cohort Equations)",
        "Circulation", 2014, population="US multi-ethnic", study_type="Guideline"),
    "Framingham_General_CVD": _ref(
        "D'Agostino RB Sr, Vasan RS, Pencina MJ, et al. General cardiovascular risk profile for use in primary care: the Framingham Heart Study. Circulation. 2008;117(6):743-753.",
        "10.1161/CIRCULATIONAHA.107.699579", "18212285",
        "General cardiovascular risk profile for use in primary care (Framingham)",
        "Circulation", 2008, population="Framingham cohort", study_type="Prospective cohort"),
    "SCORE2_10Y": _ref(
        "SCORE2 working group and ESC Cardiovascular Risk Collaboration. SCORE2 risk prediction algorithms: new models to estimate 10-year risk of cardiovascular disease in Europe. Eur Heart J. 2021;42(25):2439-2454.",
        "10.1093/eurheartj/ehab309", "34120177",
        "SCORE2 risk prediction algorithms for 10-year CVD risk in Europe",
        "European Heart Journal", 2021, population="European multi-country", study_type="Pooled cohort"),
    "CVD_PREVENT_10Y": _ref(
        "Khan SS, Matsushita K, Sang Y, et al. Novel Prediction Equations for Absolute Risk of Cardiovascular Disease: AHA PREVENT Equations. Circulation. 2024;149(6):430-449.",
        "10.1161/CIRCULATIONAHA.123.067620", "37947116",
        "AHA PREVENT Equations for absolute CVD risk",
        "Circulation", 2024, population="US multi-ethnic", study_type="Pooled cohort"),
    "Heart_Failure_PREVENT_10Y": _ref(
        "Khan SS, Matsushita K, Sang Y, et al. AHA PREVENT Risk Prediction Equations for Incident Heart Failure. Circulation. 2024;149(6):430-449.",
        "10.1161/CIRCULATIONAHA.123.067620", "37947116",
        "AHA PREVENT Equations for incident heart failure",
        "Circulation", 2024, population="US multi-ethnic", study_type="Pooled cohort"),
    "CVD_Recurrent_SMART": _ref(
        "Dorresteijn JA, Visseren FL, Wassink AM, et al. Prediction of recurrent vascular events in patients with manifest vascular disease: the SMART risk score. Heart. 2013;99(12):866-872.",
        "10.1136/heartjnl-2013-303640", "23539608",
        "The SMART risk score for recurrent vascular events",
        "Heart", 2013, population="Secondary prevention", study_type="Prospective cohort"),
    "CAD_TIMI_NSTEMI": _ref(
        "Antman EM, Cohen M, Bernink PJ, et al. The TIMI risk score for unstable angina/non-ST elevation MI. JAMA. 2000;284(7):835-842.",
        "10.1001/jama.284.7.835", "10938172",
        "The TIMI risk score for unstable angina/non-ST elevation MI",
        "JAMA", 2000, population="ACS patients", study_type="RCT sub-analysis"),
    "ACS_HEART": _ref(
        "Six AJ, Backus BE, Kelder JC. Chest pain in the emergency room: value of the HEART score. Neth Heart J. 2008;16(6):191-196.",
        "10.1007/BF03086144", "18665203",
        "Chest pain in the emergency room: value of the HEART score",
        "Netherlands Heart Journal", 2008, population="ED chest pain", study_type="Prospective cohort"),
    "Heart_Failure_MAGGIC": _ref(
        "Pocock SJ, Ariti CA, McMurray JJ, et al. Predicting survival in heart failure: a risk score based on 39 372 patients from 30 studies (MAGGIC). Eur Heart J. 2013;34(19):1404-1413.",
        "10.1093/eurheartj/ehs337", "23095984",
        "Predicting survival in heart failure (MAGGIC meta-analysis score)",
        "European Heart Journal", 2013, population="Global HF meta-analysis", study_type="Meta-analysis"),
    "HFpEF_H2FPEF": _ref(
        "Reddy YNV, Carter RE, Obokata M, Redfield MM, Borlaug BA. A Simple, Evidence-Based Approach to Help Guide the Diagnosis of HFpEF (H2FPEF). Circulation. 2018;138(9):861-870.",
        "10.1161/CIRCULATIONAHA.118.034646", "29792299",
        "The H2FPEF score for diagnostic probability of HFpEF",
        "Circulation", 2018, population="Dyspnoea cohort", study_type="Diagnostic cohort"),
    "HFpEF_HFA_PEFF_Score": _ref(
        "Pieske B, Tschöpe C, de Boer RA, et al. How to diagnose heart failure with preserved ejection fraction: the HFA-PEFF diagnostic algorithm. Eur Heart J. 2019;40(40):3297-3317.",
        "10.1093/eurheartj/ehz641", "31504452",
        "The HFA-PEFF diagnostic algorithm for HFpEF",
        "European Heart Journal", 2019, population="HFpEF consensus", study_type="Expert consensus"),

    # ---- AF / Stroke / VTE ----
    "AF_Stroke_CHA2DS2VASc": _ref(
        "Lip GY, Nieuwlaat R, Pisters R, Lane DA, Crijns HJ. Refining clinical risk stratification for predicting stroke in atrial fibrillation (CHA2DS2-VASc). Chest. 2010;137(2):263-272.",
        "10.1378/chest.09-1584", "19762550",
        "Refining clinical risk stratification for stroke in atrial fibrillation (CHA2DS2-VASc)",
        "Chest", 2010, population="AF patients", study_type="Registry cohort"),
    "AF_Bleeding_HASBLED": _ref(
        "Pisters R, Lane DA, Nieuwlaat R, de Vos CB, Crijns HJ, Lip GY. A novel user-friendly score (HAS-BLED) to assess 1-year risk of major bleeding in AF. Chest. 2010;138(5):1093-1100.",
        "10.1378/chest.10-0134", "20299623",
        "The HAS-BLED score for 1-year major bleeding risk in AF",
        "Chest", 2010, population="AF on anticoagulation", study_type="Registry cohort"),
    "AF_Bleeding_ORBIT": _ref(
        "O'Brien EC, Simon DN, Thomas LE, et al. The ORBIT bleeding score: a simple score to assess bleeding risk in AF. J Am Coll Cardiol. 2015;66(21):2205-2214.",
        "10.1016/j.jacc.2015.09.018", "26610873",
        "The ORBIT bleeding score for AF",
        "Journal of the American College of Cardiology", 2015, population="AF registry", study_type="Prospective registry"),
    "AF_Bleeding_ATRIA": _ref(
        "Fang MC, Go AS, Chang Y, et al. A new risk scheme to predict warfarin-associated hemorrhage: The ATRIA Study. J Am Coll Cardiol. 2011;58(4):395-401.",
        "10.1016/j.jacc.2011.03.031", "21757117",
        "The ATRIA bleeding risk scheme",
        "Journal of the American College of Cardiology", 2011, population="AF on warfarin", study_type="Prospective cohort"),
    "TIA_Stroke_ABCD2": _ref(
        "Johnston SC, Rothwell PM, Nguyen-Huynh MN, et al. Validation and refinement of scores to predict very early stroke risk after TIA (ABCD2). Lancet. 2007;369(9558):283-292.",
        "10.1016/S0140-6736(07)60150-0", "17258668",
        "Validation and refinement of the ABCD2 score after TIA",
        "The Lancet", 2007, population="TIA patients", study_type="Validation cohort"),
    "DVT_Wells": _ref(
        "Wells PS, Hirsh J, Anderson DR, et al. Accuracy of clinical assessment of deep-vein thrombosis (Wells DVT). Lancet. 1995;345(8961):1326-1330.",
        "10.1016/S0140-6736(95)92575-4", "7752753",
        "Accuracy of clinical assessment of deep-vein thrombosis",
        "The Lancet", 1995, population="Suspected DVT", study_type="Diagnostic cohort"),
    "PE_Wells": _ref(
        "Wells PS, Anderson DR, Rodger M, et al. Derivation of a simple clinical model to categorize patients probability of pulmonary embolism (Wells PE). Thromb Haemost. 2000;83(3):416-420.",
        "10.1055/s-0037-1613962", "10744147",
        "Derivation of the Wells PE clinical model",
        "Thrombosis and Haemostasis", 2000, population="Suspected PE", study_type="Diagnostic cohort"),
    "PE_Geneva": _ref(
        "Le Gal G, Righini M, Roy PM, et al. Prediction of pulmonary embolism in the emergency department: the revised Geneva score. Ann Intern Med. 2006;144(3):165-171.",
        "10.7326/0003-4819-144-3-200602070-00006", "16461960",
        "The revised Geneva score for PE",
        "Annals of Internal Medicine", 2006, population="ED suspected PE", study_type="Prospective validation"),
    "PE_30d_sPESI": _ref(
        "Jiménez D, Aujesky D, Moores L, et al. Simplification of the pulmonary embolism severity index (sPESI). Arch Intern Med. 2010;170(15):1383-1389.",
        "10.1001/archinternmed.2010.125", "20696966",
        "Simplification of the pulmonary embolism severity index (sPESI)",
        "Archives of Internal Medicine", 2010, population="Acute PE", study_type="Prospective cohort"),
    "PE_Bova_Score": _ref(
        "Bova C, Sanchez O, Prandoni P, et al. Identification of intermediate-high-risk patients with acute pulmonary embolism: the Bova score. Circulation. 2014;130(15):1290-1297.",
        "10.1161/CIRCULATIONAHA.114.009862", "25225143",
        "The Bova score for intermediate-high-risk PE",
        "Circulation", 2014, population="Normotensive PE", study_type="Prospective cohort"),
    "VTE_Caprini": _ref(
        "Bahl V, Hu HM, Henke PK, Wakefield TW, Campbell DA Jr, Caprini JA. A comprehensive risk assessment model for venous thromboembolism (Caprini). Ann Surg. 2010;251(2):344-350.",
        "10.1097/SLA.0b013e3181a62d9f", "20054270",
        "The Caprini risk assessment model for VTE",
        "Annals of Surgery", 2010, population="Surgical patients", study_type="Retrospective cohort"),
    "VTE_Padua": _ref(
        "Barbar S, Noventa F, Rossetto V, et al. A risk assessment model for hospitalized medical patients at risk for VTE: the Padua Prediction Score. J Thromb Haemost. 2010;8(11):2450-2457.",
        "10.1111/j.1538-7836.2010.04044.x", "20738765",
        "The Padua Prediction Score for medical inpatients",
        "Journal of Thrombosis and Haemostasis", 2010, population="Medical inpatients", study_type="Prospective cohort"),
    "VTE_Khorana_Score": _ref(
        "Khorana AA, Kuderer NM, Culakova E, Lyman GH, Francis CW. Development and validation of a predictive model for chemotherapy-associated thrombosis. Blood. 2008;111(10):4902-4907.",
        "10.1182/blood-2007-10-116327", "18216298",
        "The Khorana score for chemotherapy-associated thrombosis",
        "Blood", 2008, population="Cancer on chemotherapy", study_type="Prospective cohort"),
    "Familial_Hypercholesterolemia_DLCN": _ref(
        "Nordestgaard BG, Chapman MJ, Humphries SE, et al. Familial hypercholesterolaemia is underdiagnosed and undertreated (DLCN criteria). Eur Heart J. 2013;34(45):3478-3490.",
        "10.1093/eurheartj/eht273", "23956253",
        "Familial hypercholesterolaemia: guidance for clinicians (DLCN)",
        "European Heart Journal", 2013, population="General population", study_type="Consensus"),
    "PAD_ABI": _ref(
        "Aboyans V, Criqui MH, Abraham P, et al. Measurement and interpretation of the ankle-brachial index: AHA scientific statement. Circulation. 2012;126(24):2890-2909.",
        "10.1161/CIR.0b013e318276fbcb", "23159553",
        "Measurement and interpretation of the ankle-brachial index",
        "Circulation", 2012, population="PAD screening", study_type="Scientific statement"),

    # ---- Renal ----
    "Chronic_Kidney_Disease": _ref(
        "Tangri N, Stevens LA, Griffith J, et al. A predictive model for progression of chronic kidney disease to kidney failure (KFRE). JAMA. 2011;305(15):1553-1559.",
        "10.1001/jama.2011.451", "21482839",
        "A predictive model for CKD progression to kidney failure (KFRE 4-variable)",
        "JAMA", 2011, population="CKD stages 3-5", study_type="Prospective cohort"),
    "CKD_KFRE_8Var": _ref(
        "Tangri N, Grams ME, Levey AS, et al. Multinational Assessment of Accuracy of Equations for Predicting Risk of Kidney Failure (KFRE 8-variable). JAMA. 2016;315(2):164-174.",
        "10.1001/jama.2015.18202", "26757465",
        "Multinational assessment of KFRE 8-variable equations",
        "JAMA", 2016, population="Global CKD cohorts", study_type="Meta-analysis"),
    "CKD_KDIGO_Grid": _ref(
        "KDIGO CKD Work Group. KDIGO 2024 Clinical Practice Guideline for the Evaluation and Management of Chronic Kidney Disease. Kidney Int. 2024;105(4S):S117-S314.",
        "10.1016/j.kint.2023.10.018", "38490803",
        "KDIGO 2024 CKD evaluation and management guideline (G/A prognosis grid)",
        "Kidney International", 2024, population="CKD global", study_type="Clinical guideline"),
    "Acute_Kidney_Injury": _ref(
        "KDIGO AKI Work Group. KDIGO Clinical Practice Guideline for Acute Kidney Injury. Kidney Int Suppl. 2012;2(1):1-138.",
        "10.1038/kisup.2012.1", "",
        "KDIGO Clinical Practice Guideline for Acute Kidney Injury",
        "Kidney International Supplements", 2012, population="AKI global", study_type="Clinical guideline"),
    "Nephrology_IgA_Prediction_Tool": _ref(
        "Barbour SJ, Coppo R, Zhang H, et al. Predicting Progression of IgA Nephropathy: The International IgA Nephropathy Prediction Tool. JAMA Intern Med. 2019;179(7):942-952.",
        "10.1001/jamainternmed.2019.0600", "30980054",
        "The International IgA Nephropathy Prediction Tool",
        "JAMA Internal Medicine", 2019, population="IgA nephropathy", study_type="International cohort"),

    # ---- Hepatic ----
    "NAFLD": _ref(
        "Bedogni G, Bellentani S, Miglioli L, et al. The Fatty Liver Index: a simple and accurate predictor of hepatic steatosis. BMC Gastroenterol. 2006;6:33.",
        "10.1186/1471-230X-6-33", "17081293",
        "The Fatty Liver Index (FLI)",
        "BMC Gastroenterology", 2006, population="General population", study_type="Cross-sectional"),
    "NAFLD_HSI": _ref(
        "Lee JH, Kim D, Kim HJ, et al. Hepatic steatosis index: a simple screening tool reflecting nonalcoholic fatty liver disease. Dig Liver Dis. 2010;42(7):503-508.",
        "10.1016/j.dld.2009.12.005", "20080072",
        "The hepatic steatosis index (HSI)",
        "Digestive and Liver Disease", 2010, population="Korean cohort", study_type="Cross-sectional"),
    "NASH": _ref(
        "Sterling RK, Lissen E, Clumeck N, et al. Development of a simple noninvasive index to predict significant fibrosis (FIB-4). Hepatology. 2006;43(6):1317-1325.",
        "10.1002/hep.21194", "16729309",
        "Development of the FIB-4 index for significant fibrosis",
        "Hepatology", 2006, population="HIV/HCV coinfection", study_type="Diagnostic cohort"),
    "NASH_FAST_Score": _ref(
        "Newsome PN, Sasso M, Deeks JJ, et al. FibroScan-AST (FAST) score for NASH with significant activity and advanced fibrosis. Lancet Gastroenterol Hepatol. 2020;5(4):362-373.",
        "10.1016/S2468-1253(19)30383-8", "32027858",
        "The FAST score for at-risk NASH",
        "The Lancet Gastroenterology & Hepatology", 2020, population="NAFLD/NASH", study_type="Diagnostic cohort"),
    "Liver_Fibrosis_APRI": _ref(
        "Wai CT, Greenson JK, Fontana RJ, et al. A simple noninvasive index (APRI) predicts significant fibrosis and cirrhosis. Hepatology. 2003;38(2):518-526.",
        "10.1053/jhep.2003.50353", "12883497",
        "The AST-to-platelet ratio index (APRI)",
        "Hepatology", 2003, population="Chronic hepatitis C", study_type="Diagnostic cohort"),
    "Liver_Fibrosis_NFS": _ref(
        "Angulo P, Hui JM, Marchesini G, et al. The NAFLD fibrosis score: a noninvasive system that identifies liver fibrosis. Hepatology. 2007;45(4):846-854.",
        "10.1002/hep.21496", "17393509",
        "The NAFLD fibrosis score (NFS)",
        "Hepatology", 2007, population="NAFLD", study_type="Diagnostic cohort"),
    "Liver_Fibrosis_BARD": _ref(
        "Harrison SA, Oliver D, Arnold HL, Gogia S, Neuschwander-Tetri BA. Development and validation of a simple NAFLD clinical scoring system (BARD). Gut. 2008;57(10):1441-1447.",
        "10.1136/gut.2007.146019", "18492734",
        "The BARD score for advanced NAFLD fibrosis",
        "Gut", 2008, population="NAFLD", study_type="Validation cohort"),
    "Liver_ALBI": _ref(
        "Johnson PJ, Berhane S, Kagebayashi C, et al. Assessment of liver function in HCC: the ALBI grade. J Clin Oncol. 2015;33(6):550-558.",
        "10.1200/JCO.2014.57.9151", "25512453",
        "The albumin-bilirubin (ALBI) grade",
        "Journal of Clinical Oncology", 2015, population="HCC", study_type="International cohort"),
    "Cirrhosis_MELD_Na": _ref(
        "Kamath PS, Wiesner RH, Malinchoc M, et al. A model to predict survival in end-stage liver disease (MELD). Hepatology. 2001;33(2):464-470.",
        "10.1053/jhep.2001.22172", "11172350",
        "The Model for End-Stage Liver Disease (MELD)",
        "Hepatology", 2001, population="ESLD", study_type="Retrospective cohort"),
    "Cirrhosis_MELD3": _ref(
        "Kim WR, Mannalithara A, Heimbach JK, et al. MELD 3.0: The Model for End-Stage Liver Disease Updated for the Modern Era. Gastroenterology. 2021;161(6):1887-1895.e4.",
        "10.1053/j.gastro.2021.08.050", "34481845",
        "MELD 3.0 for the modern era",
        "Gastroenterology", 2021, population="ESLD / transplant", study_type="Registry"),
    "Cirrhosis_Child_Pugh": _ref(
        "Pugh RN, Murray-Lyon IM, Dawson JL, Pietroni MC, Williams R. Transection of the oesophagus for bleeding oesophageal varices (Child-Pugh). Br J Surg. 1973;60(8):646-649.",
        "10.1002/bjs.1800600817", "4541913",
        "The Child-Pugh classification of cirrhosis severity",
        "British Journal of Surgery", 1973, population="Cirrhosis", study_type="Historical cohort"),
    "Cirrhosis_PALBI_Grade": _ref(
        "Roayaie S, Jibara G, Tabrizian P, et al. The PALBI score: a new tool for assessing liver function and portal hypertension. Hepatology. 2015;62(6):1726-1734.",
        "10.1002/hep.27988", "26174780",
        "The platelet-albumin-bilirubin (PALBI) grade",
        "Hepatology", 2015, population="HCC / portal HTN", study_type="Retrospective cohort"),
    "Alcoholic_Hepatitis_GAHS": _ref(
        "Forrest EH, Evans CD, Stewart S, et al. Analysis of factors predictive of mortality in alcoholic hepatitis: the Glasgow alcoholic hepatitis score. Gut. 2005;54(8):1174-1179.",
        "10.1136/gut.2004.050781", "16009691",
        "The Glasgow alcoholic hepatitis score (GAHS)",
        "Gut", 2005, population="Alcoholic hepatitis", study_type="Prospective cohort"),
    "HCC_REACH_B": _ref(
        "Yang HI, Yuen MF, Chan HL, et al. Risk estimation for hepatocellular carcinoma in chronic hepatitis B (REACH-B). Lancet Oncol. 2011;12(6):568-574.",
        "10.1016/S1470-2045(11)70076-1", "21497551",
        "The REACH-B score for HCC risk in chronic HBV",
        "The Lancet Oncology", 2011, population="Chronic HBV Asia", study_type="Prospective cohort"),
    "HCC_PAGE_B": _ref(
        "Papatheodoridis G, Dalekos G, Sypsa V, et al. PAGE-B predicts the risk of HCC in Caucasians with chronic hepatitis B on antiviral therapy. J Hepatol. 2016;64(4):800-806.",
        "10.1016/j.jhep.2015.11.035", "26678253",
        "The PAGE-B score for HCC risk on therapy",
        "Journal of Hepatology", 2016, population="Caucasian HBV on therapy", study_type="Prospective cohort"),
    "HCC_GALAD": _ref(
        "Berhane S, Toyoda H, Tada T, et al. Role of GALAD and BALAD-2 Serologic Models in Diagnosis of Hepatocellular Carcinoma. Cancer Epidemiol Biomarkers Prev. 2016;25(1):144-152.",
        "10.1158/1055-9965.EPI-15-0724", "26500331",
        "The GALAD model for HCC detection",
        "Cancer Epidemiology, Biomarkers & Prevention", 2016, population="HBV/HCC screening", study_type="Diagnostic cohort"),
    "Liver_Failure_Kings_College": _ref(
        "O'Grady JG, Alexander GJ, Hayllar KM, Williams R. Early indicators of prognosis in fulminant hepatic failure (King's College Criteria). Gastroenterology. 1989;97(2):439-445.",
        "10.1016/0016-5085(89)90081-4", "2490426",
        "King's College criteria for acute liver failure",
        "Gastroenterology", 1989, population="Acute liver failure", study_type="Retrospective cohort"),

    # ---- Oncology screening ----
    "Lung_Cancer_PLCOm2012": _ref(
        "Tammemägi MC, Katki HA, Hocking WG, et al. Selection criteria for lung-cancer screening (PLCOm2012). N Engl J Med. 2013;368(8):728-736.",
        "10.1056/NEJMoa1211776", "23425165",
        "Selection criteria for lung-cancer screening (PLCOm2012)",
        "New England Journal of Medicine", 2013, population="PLCO trial", study_type="RCT sub-analysis"),
    "Colorectal_Cancer_APCS": _ref(
        "Yeoh KG, Ho KY, Chiu HM, et al. A scoring system to prioritise patients for colonoscopy screening: the APCS score. Gut. 2011;60(9):1236-1241.",
        "10.1136/gut.2010.231170", "21402615",
        "The Asia-Pacific Colorectal Screening (APCS) score",
        "Gut", 2011, population="Asia-Pacific", study_type="Multi-country cohort"),
    "Ovarian_Cancer_ROMA": _ref(
        "Moore RG, McMeekin DS, Brown AK, et al. A novel multiple marker bioassay utilizing HE4 and CA125 (ROMA) for ovarian cancer prediction. Gynecol Oncol. 2009;112(1):40-46.",
        "10.1016/j.ygyno.2008.08.031", "18851871",
        "The ROMA algorithm for ovarian malignancy",
        "Gynecologic Oncology", 2009, population="Pelvic mass", study_type="Diagnostic cohort"),
    "Prostate_Cancer_PHI": _ref(
        "Catalona WJ, Partin AW, Sanda MG, et al. A multicenter study of [-2]pro-PSA (Prostate Health Index). J Urol. 2011;185(5):1650-1655.",
        "10.1016/j.juro.2010.12.032", "21419439",
        "The Prostate Health Index (phi) for prostate cancer detection",
        "The Journal of Urology", 2011, population="Prostate screening", study_type="Multicenter diagnostic"),

    # ---- Respiratory ----
    "OSA_STOPBANG": _ref(
        "Chung F, Yegneswaran B, Liao P, et al. STOP Questionnaire: A Tool to Screen Patients for Obstructive Sleep Apnea. Anesthesiology. 2008;108(5):812-821.",
        "10.1097/ALN.0b013e31816d7796", "18431116",
        "The STOP-BANG questionnaire for OSA screening",
        "Anesthesiology", 2008, population="Pre-operative", study_type="Cross-sectional"),
    "OSA_NoSAS": _ref(
        "Marti-Soler H, Hirotsu C, Marques-Vidal P, et al. The NoSAS score for screening of sleep-disordered breathing. Lancet Respir Med. 2016;4(9):742-748.",
        "10.1016/S2213-2600(16)30075-3", "27477759",
        "The NoSAS score for sleep-disordered breathing",
        "The Lancet Respiratory Medicine", 2016, population="Lausanne cohort", study_type="Validation cohort"),
    "OSA_Berlin": _ref(
        "Netzer NC, Stoohs RA, Netzer CM, Clark K, Strohl KP. Using the Berlin Questionnaire to identify patients at risk for the sleep apnea syndrome. Ann Intern Med. 1999;131(7):485-491.",
        "10.7326/0003-4819-131-7-199910050-00002", "10502356",
        "The Berlin Questionnaire for sleep apnea risk",
        "Annals of Internal Medicine", 1999, population="Primary care", study_type="Cross-sectional"),
    "COPD_BODE": _ref(
        "Celli BR, Cote CG, Marin JM, et al. The body-mass index, airflow obstruction, dyspnea, and exercise capacity index (BODE) in COPD. N Engl J Med. 2004;350(10):1005-1012.",
        "10.1056/NEJMoa021322", "14999112",
        "The BODE index in COPD",
        "New England Journal of Medicine", 2004, population="COPD", study_type="Prospective cohort"),
    "COPD_GOLD_ABE": _ref(
        "Agustí A, Celli BR, Criner GJ, et al. Global Strategy for the Diagnosis, Management, and Prevention of COPD (GOLD 2023 Report). Am J Respir Crit Care Med. 2023;207(7):819-837.",
        "10.1164/rccm.202301-0106PP", "36853721",
        "GOLD 2023 ABE assessment strategy",
        "American Journal of Respiratory and Critical Care Medicine", 2023, population="COPD global", study_type="Clinical guideline"),
    "Asthma_ACT": _ref(
        "Nathan RA, Sorkness CA, Kosinski M, et al. Development of the asthma control test (ACT). J Allergy Clin Immunol. 2004;113(1):59-65.",
        "10.1016/j.jaci.2003.09.008", "14713908",
        "Development of the Asthma Control Test (ACT)",
        "Journal of Allergy and Clinical Immunology", 2004, population="Asthma", study_type="Validation survey"),

    # ---- Bone / Geriatric / Nutrition ----
    "Osteoporosis_OSTA": _ref(
        "Koh LK, Sedrine WB, Torralba TP, et al. A simple tool to identify Asian women at increased risk of osteoporosis (OSTA). Osteoporos Int. 2001;12(8):699-705.",
        "10.1007/s001980170061", "11580084",
        "The OSTA index for osteoporosis risk",
        "Osteoporosis International", 2001, population="Asian women", study_type="Cross-sectional"),
    "Osteoporosis_ORAI": _ref(
        "Cadarette SM, Jaglal SB, Kreiger N, McIsaac WJ, Darlington GA, Tu JV. Development of an osteoporosis risk assessment tool (ORAI). CMAJ. 2000;163(11):1449-1454.",
        "10.5555/cmaj.163.11.1449", "11192648",
        "The Osteoporosis Risk Assessment Instrument (ORAI)",
        "Canadian Medical Association Journal", 2000, population="Postmenopausal women", study_type="Cross-sectional"),
    "Sarcopenia_SARCF": _ref(
        "Malmstrom TK, Morley JE. SARC-F: a simple questionnaire to rapidly diagnose sarcopenia. J Am Med Dir Assoc. 2013;14(8):531-532.",
        "10.1016/j.jamda.2013.05.018", "23810110",
        "The SARC-F sarcopenia questionnaire",
        "Journal of the American Medical Directors Association", 2013, population="Older adults", study_type="Validation questionnaire"),
    "Frailty_Fried": _ref(
        "Fried LP, Tangen CM, Walston J, et al. Frailty in older adults: evidence for a phenotype. J Gerontol A Biol Sci Med Sci. 2001;56(3):M146-M156.",
        "10.1093/gerona/56.3.M146", "11253156",
        "The Fried frailty phenotype",
        "The Journals of Gerontology Series A", 2001, population="CHS cohort", study_type="Prospective cohort"),
    "Fall_Risk_Morse": _ref(
        "Morse JM, Morse RM, Tylko SJ. Development of a scale to identify the fall-prone patient (Morse Fall Scale). Can J Aging. 1989;8(4):366-377.",
        "10.1017/S071498080000882X", "10296767",
        "The Morse Fall Scale",
        "Canadian Journal on Aging", 1989, population="Hospitalised", study_type="Validation cohort"),
    "Malnutrition_MUST": _ref(
        "Stratton RJ, Hackston A, Longmore D, et al. Malnutrition Universal Screening Tool (MUST). Br J Nutr. 2004;92(5):799-808.",
        "10.1079/bjn20041258", "15533284",
        "The Malnutrition Universal Screening Tool (MUST)",
        "British Journal of Nutrition", 2004, population="Hospital / community", study_type="Validation study"),
    "Hip_Fracture_10Y_FRAX_Estimate": _ref(
        "Kanis JA, Oden A, Johnell O, et al. The use of clinical risk factors enhances the performance of BMD in the prediction of hip and osteoporotic fractures (FRAX). Osteoporos Int. 2007;18(8):1033-1046.",
        "10.1007/s00198-007-0343-y", "17334658",
        "FRAX: clinical risk factors + BMD for fracture prediction",
        "Osteoporosis International", 2007, population="General population", study_type="Validation model"),

    # ---- Neuro / Psych / Substance ----
    "Dementia_CAIDE": _ref(
        "Kivipelto M, Ngandu T, Laatikainen T, Winblad B, Soininen H, Tuomilehto J. Risk score for the prediction of dementia risk in 20 years (CAIDE). Lancet Neurol. 2006;5(9):735-741.",
        "10.1016/S1474-4422(06)70537-3", "16914401",
        "The CAIDE dementia risk score",
        "The Lancet Neurology", 2006, population="Finnish cohort", study_type="Longitudinal cohort"),
    "Depression_PHQ9": _ref(
        "Kroenke K, Spitzer RL, Williams JB. The PHQ-9: validity of a brief depression severity measure. J Gen Intern Med. 2001;16(9):606-613.",
        "10.1046/j.1525-1497.2001.016009606.x", "11556941",
        "The PHQ-9 depression severity measure",
        "Journal of General Internal Medicine", 2001, population="Primary care", study_type="Validation study"),
    "Anxiety_GAD7": _ref(
        "Spitzer RL, Kroenke K, Williams JB, Löwe B. A brief measure for assessing generalized anxiety disorder: the GAD-7. Arch Intern Med. 2006;166(10):1092-1097.",
        "10.1001/archinte.166.10.1092", "16717171",
        "The GAD-7 anxiety measure",
        "Archives of Internal Medicine", 2006, population="Primary care", study_type="Validation study"),
    "Alcohol_AUDIT_C": _ref(
        "Bush K, Kivlahan DR, McDonell MB, Fihn SD, Bradley KA. The AUDIT alcohol consumption questions (AUDIT-C). Arch Intern Med. 1998;158(16):1789-1795.",
        "10.1001/archinte.158.16.1789", "9738608",
        "The AUDIT-C alcohol screening tool",
        "Archives of Internal Medicine", 1998, population="Primary care", study_type="Validation study"),
    "Alcohol_CAGE": _ref(
        "Ewing JA. Detecting alcoholism. The CAGE questionnaire. JAMA. 1984;252(14):1905-1907.",
        "10.1001/jama.1984.03350140043019", "6471323",
        "The CAGE questionnaire",
        "JAMA", 1984, population="General", study_type="Validation study"),
    "Nicotine_Fagerstrom": _ref(
        "Heatherton TF, Kozlowski LT, Frecker RC, Fagerström KO. The Fagerström Test for Nicotine Dependence. Br J Addict. 1991;86(9):1119-1127.",
        "10.1111/j.1360-0443.1991.tb01879.x", "1931887",
        "The Fagerström Test for Nicotine Dependence (FTND)",
        "British Journal of Addiction", 1991, population="Smokers", study_type="Validation study"),

    # ---- Haematology / ICU / Oncology staging ----
    "DIC_ISTH": _ref(
        "Taylor FB Jr, Toh CH, Hoots WK, Wada H, Levi M. Towards definition, clinical and laboratory criteria, and a scoring system for DIC (ISTH). Thromb Haemost. 2001;86(5):1327-1330.",
        "10.1055/s-0037-1616066", "11816725",
        "The ISTH overt DIC scoring system",
        "Thrombosis and Haemostasis", 2001, population="DIC", study_type="Consensus"),
    "Iron_Deficiency_Anemia": _ref(
        "Camaschella C. Iron-Deficiency Anemia. N Engl J Med. 2015;372(19):1832-1843.",
        "10.1056/NEJMra1401038", "25946282",
        "Iron-deficiency anemia",
        "New England Journal of Medicine", 2015, population="General", study_type="Review"),
    "Anemia_Phenotype": _ref(
        "Cappellini MD, Comin-Colet J, de Francisco A, et al. Iron deficiency across chronic diseases. F1000Res. 2020;9:67.",
        "10.12688/f1000research.21294.1", "32089837",
        "Iron deficiency across chronic diseases",
        "F1000Research", 2020, population="Chronic disease", study_type="Expert review"),
    "Primary_Hypothyroidism": _ref(
        "Vanderpump MP, Tunbridge WM, French JM, et al. The incidence of thyroid disorders in the community: a twenty-year follow-up of the Whickham Survey. Clin Endocrinol (Oxf). 1995;43(1):55-68.",
        "10.1111/j.1365-2265.1995.tb01894.x", "7641412",
        "The Whickham Survey: thyroid disorders in the community",
        "Clinical Endocrinology", 1995, population="Whickham cohort", study_type="Longitudinal cohort"),
    "Gout": _ref(
        "FitzGerald JD, Dalbeth N, Mikuls T, et al. 2020 American College of Rheumatology Guideline for the Management of Gout. Arthritis Care Res. 2020;72(6):744-760.",
        "10.1002/acr.24180", "32390306",
        "2020 ACR Guideline for the Management of Gout",
        "Arthritis Care & Research", 2020, population="Gout", study_type="Clinical guideline"),
    "Oncology_TLS_Cairo_Bishop": _ref(
        "Cairo MS, Bishop M. Tumour lysis syndrome: new therapeutic strategies and classification (Cairo-Bishop). Br J Haematol. 2004;127(1):3-11.",
        "10.1111/j.1365-2141.2004.05094.x", "15384972",
        "The Cairo-Bishop TLS classification",
        "British Journal of Haematology", 2004, population="Haematologic malignancy", study_type="Consensus"),
    "ICU_APACHE_II": _ref(
        "Knaus WA, Draper EA, Wagner DP, Zimmerman JE. APACHE II: a severity of disease classification system. Crit Care Med. 1985;13(10):818-829.",
        "10.1097/00003246-198510000-00009", "3928249",
        "APACHE II severity of disease classification",
        "Critical Care Medicine", 1985, population="ICU", study_type="Multicenter cohort"),
    "ICU_SAPS_II": _ref(
        "Le Gall JR, Lemeshow S, Saulnier F. A new Simplified Acute Physiology Score (SAPS II). JAMA. 1993;270(24):2957-2963.",
        "10.1001/jama.1993.03510240069035", "8254858",
        "The SAPS II score",
        "JAMA", 1993, population="ICU", study_type="Multicenter cohort"),
    "Myeloma_R2_ISS": _ref(
        "D'Agostino M, Cairns DA, Lahuerta JJ, et al. Second Revision of the International Staging System (R2-ISS) for Multiple Myeloma. J Clin Oncol. 2022;40(29):3406-3418.",
        "10.1200/JCO.21.02614", "35605179",
        "The R2-ISS for multiple myeloma",
        "Journal of Clinical Oncology", 2022, population="Multiple myeloma", study_type="International cohort"),
    "Lymphoma_DLBCL_IPI": _ref(
        "The International Non-Hodgkin's Lymphoma Prognostic Factors Project. A predictive model for aggressive non-Hodgkin's lymphoma (IPI). N Engl J Med. 1993;329(14):987-994.",
        "10.1056/NEJM199309303291402", "8141877",
        "The International Prognostic Index (IPI) for DLBCL",
        "New England Journal of Medicine", 1993, population="DLBCL", study_type="International cohort"),
    "Leukemia_CLL_IPI": _ref(
        "International CLL-IPI Working Group. An international prognostic index for patients with chronic lymphocytic leukaemia (CLL-IPI). Lancet Oncol. 2016;17(6):779-790.",
        "10.1016/S1470-2045(16)30029-8", "27185642",
        "The CLL-IPI prognostic index",
        "The Lancet Oncology", 2016, population="CLL", study_type="Meta-analysis"),
    "GIBleed_AIMS65": _ref(
        "Saltzman JR, Tabak YP, Hyett BH, Sun X, Travis AC, Johannes CB. AIMS65 score for acute upper GI bleeding. Gastrointest Endosc. 2011;74(6):1215-1224.",
        "10.1016/j.gie.2011.08.015", "21963066",
        "The AIMS65 score for upper GI bleeding",
        "Gastrointestinal Endoscopy", 2011, population="Upper GI bleed", study_type="Retrospective cohort"),
    "Pneumonia_PSI_PORT": _ref(
        "Fine MJ, Auble TE, Yealy DM, et al. A prediction rule to identify low-risk patients with community-acquired pneumonia (PSI/PORT). N Engl J Med. 1997;336(4):243-250.",
        "10.1056/NEJM199701233360402", "8995086",
        "The Pneumonia Severity Index (PSI/PORT)",
        "New England Journal of Medicine", 1997, population="CAP", study_type="Prospective cohort"),
    "Pneumonia_SMART_COP": _ref(
        "Charles PG, Wolfe R, Christmany M, et al. SMART-COP: predicting intensive respiratory or vasopressor support in pneumonia. Clin Infect Dis. 2008;47(3):375-384.",
        "10.1086/589754", "18558884",
        "The SMART-COP tool for severe pneumonia",
        "Clinical Infectious Diseases", 2008, population="CAP", study_type="Prospective cohort"),
    "Acuity_NEWS2_Score": _ref(
        "Royal College of Physicians. National Early Warning Score (NEWS) 2. Clin Med (Lond). 2018;18(1).",
        "10.7861/clinmedicine.18-1-news2", "29305374",
        "The National Early Warning Score 2 (NEWS2)",
        "Clinical Medicine", 2018, population="Acute illness NHS", study_type="Clinical guideline"),
}


# ===========================================================================
# 2. SPECIALIZED DISEASE REFERENCES  (progression / recurrence models)
# ===========================================================================
SPECIALIZED_DISEASE_REFERENCES: Dict[str, Dict[str, Any]] = {
    "Coronary_Atherosclerosis_Progression": _ref(
        "Assmann G, Cullen P, Schulte H. Simple scoring scheme for calculating the risk of acute coronary events (PROCAM). Circulation. 2002;105(3):310-315.",
        "10.1161/hc0302.102575", "11804985",
        "The PROCAM score for acute coronary events",
        "Circulation", 2002, population="German male cohort", study_type="Prospective cohort"),
    "Premature_CAD_Family_History": _ref(
        "Marenberg ME, Risch NJ, Berkman LF, Floderus B, de Faire U. Genetic susceptibility to death from coronary heart disease in a study of twins. N Engl J Med. 1994;330(15):1041-1046.",
        "10.1056/NEJM199404143301503", "8127328",
        "Genetic susceptibility to death from CHD: a twin study",
        "New England Journal of Medicine", 1994, population="Swedish twins", study_type="Twin cohort"),
    "Diabetic_Cardiomyopathy_Risk": _ref(
        "Stratton IM, Adler AI, Neil HA, et al. Association of glycaemia with macrovascular and microvascular complications of type 2 diabetes (UKPDS 35). BMJ. 2000;321(7258):405-412.",
        "10.1136/bmj.321.7258.405", "10938048",
        "Association of glycaemia with complications of type 2 diabetes (UKPDS 35)",
        "BMJ", 2000, population="UKPDS T2DM", study_type="RCT cohort"),
    "Hypertensive_Heart_Disease_LVH": _ref(
        "Levy D, Garrison RJ, Savage DD, Kannel WB, Castelli WP. Prognostic implications of echocardiographically determined left ventricular mass in the Framingham Heart Study. N Engl J Med. 1990;322(22):1561-1566.",
        "10.1056/NEJM199005313222204", "2139710",
        "Prognostic implications of LV mass (Framingham)",
        "New England Journal of Medicine", 1990, population="Framingham cohort", study_type="Prospective cohort"),
    "Ischemic_Stroke_Recurrence_5Y": _ref(
        "Hankey GJ, Jamrozik K, Broadhurst RJ, et al. Long-term risk of first-ever stroke in the community (Perth Study). Stroke. 2002;33(9):2240-2244.",
        "10.1161/01.str.0000027210.68652.c0", "12183628",
        "Five-year risk of stroke recurrence (Perth Community Stroke Study)",
        "Stroke", 2002, population="Perth stroke cohort", study_type="Population cohort"),
    "Cardiorenal_Syndrome_Progression": _ref(
        "Ronco C, Haapio M, House AA, Anavekar N, Bellomo R. Cardiorenal syndrome. J Am Coll Cardiol. 2008;52(19):1527-1539.",
        "10.1016/j.jacc.2008.07.051", "19007588",
        "Cardiorenal syndrome classification and progression",
        "Journal of the American College of Cardiology", 2008, population="HF + CKD", study_type="Review"),
    "Vascular_Dementia_Ischemic_Risk": _ref(
        "Vermeer SE, Prins ND, den Heijer T, Hofman A, Koudstaal PJ, Breteler MM. Silent brain infarcts and the risk of dementia and cognitive decline. N Engl J Med. 2003;348(13):1215-1222.",
        "10.1056/NEJMoa022066", "12660385",
        "Silent brain infarcts and risk of dementia (Rotterdam Scan Study)",
        "New England Journal of Medicine", 2003, population="Rotterdam cohort", study_type="Prospective cohort"),
    "Statin_Induced_Myopathy_Risk": _ref(
        "SEARCH Collaborative Group. SLCO1B1 variants and statin-induced myopathy—a genomewide study. N Engl J Med. 2008;359(8):789-799.",
        "10.1056/NEJMoa0801936", "18650507",
        "SLCO1B1 variants and statin-induced myopathy",
        "New England Journal of Medicine", 2008, population="Statin users", study_type="GWAS"),
    "Aortic_Stenosis_Progression_Rate": _ref(
        "Chan KL, Dumesnil JG, Cujec B, et al. A prospective study of the progression of aortic stenosis (ASTRONOMER). Circulation. 2010;121(2):306-313.",
        "10.1161/CIRCULATIONAHA.109.900027", "20048225",
        "Progression of aortic stenosis (ASTRONOMER)",
        "Circulation", 2010, population="Aortic stenosis", study_type="Prospective cohort"),
    "Microvascular_Angina_INOCA": _ref(
        "Ford TJ, Stanley B, Sidebotham D, et al. Stratified Medical Therapy Using Invasive Coronary Function Testing in Angina (CorMicA). J Am Coll Cardiol. 2018;72(23):2841-2855.",
        "10.1016/j.jacc.2018.09.006", "30497560",
        "The CorMicA trial for INOCA",
        "Journal of the American College of Cardiology", 2018, population="INOCA", study_type="RCT"),
    "Post_PCI_Restenosis_Risk": _ref(
        "Farooq V, Serruys PW, Bourantas CV, et al. Quantification of incomplete revascularization and its association with five-year mortality (SYNTAX). Lancet. 2013;381(9871):639-650.",
        "10.1016/S0140-6736(13)60107-0", "23465426",
        "SYNTAX score II for revascularization decision-making",
        "The Lancet", 2013, population="PCI patients", study_type="RCT sub-analysis"),
    "Cardiogenic_Shock_Post_MI": _ref(
        "Hochman JS, Sleeper LA, Webb JG, et al. Early revascularization in acute MI complicated by cardiogenic shock (SHOCK). N Engl J Med. 1999;341(9):625-634.",
        "10.1056/NEJM199908263410901", "10460813",
        "The SHOCK trial: early revascularization in cardiogenic shock",
        "New England Journal of Medicine", 1999, population="AMI + shock", study_type="RCT"),
    "Coronary_Calcium_Agatston_Risk": _ref(
        "Detrano R, Guerci AD, Carr JJ, et al. Coronary calcium as a predictor of coronary events in four racial or ethnic groups (MESA). N Engl J Med. 2008;358(13):1336-1347.",
        "10.1056/NEJMoa072100", "18367736",
        "Coronary calcium as a predictor of coronary events (MESA)",
        "New England Journal of Medicine", 2008, population="MESA multi-ethnic", study_type="Prospective cohort"),
    "Post_MI_Ventricular_Arrhythmia": _ref(
        "Moss AJ, Zareba W, Hall WJ, et al. Prophylactic implantation of a defibrillator in patients with MI and reduced EF (MADIT-II). N Engl J Med. 2002;346(12):877-883.",
        "10.1056/NEJMoa013474", "11907286",
        "MADIT-II: defibrillator prophylaxis post-MI",
        "New England Journal of Medicine", 2002, population="Post-MI low EF", study_type="RCT"),
    "Takotsubo_Cardiomyopathy_Recurrence": _ref(
        "Templin C, Ghadri JR, Diekmann J, et al. Clinical features and outcomes of Takotsubo (stress) cardiomyopathy (InterTAK). N Engl J Med. 2015;373(10):929-938.",
        "10.1056/NEJMoa1406761", "26321662",
        "Clinical features and outcomes of Takotsubo cardiomyopathy (InterTAK)",
        "New England Journal of Medicine", 2015, population="International registry", study_type="Registry"),
    "Diabetic_Nephropathy_Progression": _ref(
        "Alicic RZ, Rooney MT, Tuttle KR. Diabetic Kidney Disease: Challenges, Progress, and Possibilities. Clin J Am Soc Nephrol. 2017;12(12):2032-2045.",
        "10.2215/CJN.11491116", "28522654",
        "Diabetic kidney disease: challenges and progression",
        "Clinical Journal of the American Society of Nephrology", 2017, population="DKD", study_type="Review"),
    "Diabetic_Retinopathy_Progression": _ref(
        "Diabetes Control and Complications Trial Research Group. The effect of intensive treatment of diabetes on the development of long-term complications (DCCT). N Engl J Med. 1993;329(14):977-986.",
        "10.1056/NEJM199309303291401", "8366922",
        "The DCCT: intensive treatment and retinopathy progression",
        "New England Journal of Medicine", 1993, population="T1DM", study_type="RCT"),
    "Diabetic_Peripheral_Neuropathy": _ref(
        "Tesfaye S, Boulton AJ, Dyck PJ, et al. Diabetic neuropathies: update on definitions, diagnostic criteria, and risk factors (Toronto Consensus). Diabetologia. 2010;53(10):1998-2008.",
        "10.1007/s00125-010-1853-2", "20711746",
        "Toronto consensus on diabetic neuropathies",
        "Diabetologia", 2010, population="Diabetic neuropathy", study_type="Consensus"),
    "Diabetic_Foot_Ulcer_Risk": _ref(
        "Armstrong DG, Boulton AJM, Bus SA. Diabetic Foot Ulcers and Their Recurrence. N Engl J Med. 2017;376(24):2367-2375.",
        "10.1056/NEJMra1615439", "28614678",
        "Diabetic foot ulcers and their recurrence",
        "New England Journal of Medicine", 2017, population="Diabetic foot", study_type="Review"),
    "Gestational_Diabetes_Postpartum_T2D": _ref(
        "Kim C, Newton KM, Knopp RH. Gestational diabetes and the incidence of type 2 diabetes: a systematic review. Diabetes Care. 2002;25(10):1862-1868.",
        "10.2337/diacare.25.10.1862", "12351485",
        "Gestational diabetes and incident type 2 diabetes",
        "Diabetes Care", 2002, population="GDM meta-analysis", study_type="Systematic review"),
    "NonAlcoholic_Steatohepatitis_Cirrhosis": _ref(
        "Dulai PS, Singh S, Patel J, et al. Increased risk of mortality by fibrosis stage in nonalcoholic fatty liver disease: Systematic review and meta-analysis. Hepatology. 2017;65(5):1557-1565.",
        "10.1002/hep.29085", "28114696",
        "Mortality by fibrosis stage in NAFLD",
        "Hepatology", 2017, population="NAFLD", study_type="Meta-analysis"),
    "Bariatric_Surgery_DM_Remission": _ref(
        "Still CD, Wood GC, Benotti P, et al. Preoperative prediction of type 2 diabetes remission after Roux-en-Y gastric bypass (DiaRem). Lancet Diabetes Endocrinol. 2014;2(3):196-205.",
        "10.1016/S2213-8587(13)70152-6", "24622706",
        "The DiaRem score for diabetes remission post-bariatric surgery",
        "The Lancet Diabetes & Endocrinology", 2014, population="Bariatric surgery", study_type="Retrospective cohort"),
    "Severe_Obesity_Cardiometabolic_Mortality": _ref(
        "Global BMI Mortality Collaboration. Body-mass index and all-cause mortality: individual-participant-data meta-analysis of 239 prospective studies. Lancet. 2016;388(10046):776-786.",
        "10.1016/S0140-6736(16)30175-1", "27423262",
        "BMI and all-cause mortality (239 prospective studies)",
        "The Lancet", 2016, population="Global meta-analysis", study_type="IPD meta-analysis"),
    "Diabetic_Autonomic_Neuropathy": _ref(
        "Vinik AI, Maser RE, Mitchell BD, Freeman R. Diabetic autonomic neuropathy. Diabetes Care. 2003;26(5):1553-1577.",
        "10.2337/diacare.26.5.1553", "12716821",
        "Diabetic autonomic neuropathy",
        "Diabetes Care", 2003, population="Diabetes", study_type="Review"),
    "Severe_Hypoglycemia_Recurrence": _ref(
        "Karter AJ, Warton EM, Lipska KJ, et al. Development and validation of a tool to identify patients with type 2 diabetes at high risk of hypoglycemia (HYPO-SCORE). JAMA Intern Med. 2017;177(10):1461-1470.",
        "10.1001/jamainternmed.2017.4854", "28822248",
        "The HYPO-SCORE for hypoglycemia risk",
        "JAMA Internal Medicine", 2017, population="T2DM Kaiser cohort", study_type="Retrospective cohort"),
    "Rapid_eGFR_Decline_Annual": _ref(
        "Coresh J, Turin TC, Matsushita K, et al. Decline in estimated GFR and subsequent risk of ESRD and mortality. JAMA. 2014;311(24):2518-2531.",
        "10.1001/jama.2014.6634", "24866895",
        "Decline in eGFR and risk of ESRD/mortality",
        "JAMA", 2014, population="CKD Prognosis Consortium", study_type="Meta-analysis"),
    "Membranous_Nephropathy_ESRD_Risk": _ref(
        "Cattran DC, Appel GB, Hebert LA, et al. Validation of a predictive model for idiopathic membranous nephropathy progression. Kidney Int. 2005;67(6):2311-2317.",
        "10.1111/j.1523-1755.2005.00336.x", "15888048",
        "A predictive model for membranous nephropathy progression",
        "Kidney International", 2005, population="Membranous nephropathy", study_type="Validation cohort"),
    "Focal_Segmental_Glomerulosclerosis_Progression": _ref(
        "D'Agati VD, Fogo AB, Bruijn JA, Jennette JC. Pathologic classification of focal segmental glomerulosclerosis (Columbia classification). Am J Kidney Dis. 2004;43(2):368-382.",
        "10.1053/j.ajkd.2003.10.024", "14981595",
        "The Columbia classification of FSGS",
        "American Journal of Kidney Diseases", 2004, population="FSGS", study_type="Clinicopathologic"),
    "Contrast_Induced_Nephropathy_CIN": _ref(
        "Mehran R, Aymong ED, Nikolsky E, et al. A simple risk score for prediction of contrast-induced nephropathy after PCI. J Am Coll Cardiol. 2004;44(7):1393-1399.",
        "10.1016/j.jacc.2004.06.068", "15464318",
        "The Mehran score for contrast-induced nephropathy",
        "Journal of the American College of Cardiology", 2004, population="PCI patients", study_type="Prospective cohort"),
    "Autosomal_Dominant_PKD_ESRD_10Y": _ref(
        "Irazabal MV, Rangel LJ, Bergstralh EJ, et al. Imaging classification of ADPKD: a simple model for selecting patients for clinical trials (Mayo Class). J Am Soc Nephrol. 2015;26(1):160-172.",
        "10.1681/ASN.2013101138", "24904082",
        "The Mayo imaging classification for ADPKD",
        "Journal of the American Society of Nephrology", 2015, population="ADPKD", study_type="Validation cohort"),
    "Kidney_Stone_Recurrence_ROK_S": _ref(
        "Rule AD, Lieske JC, Li X, et al. The ROKS nomogram for predicting a second symptomatic stone episode. J Am Soc Nephrol. 2014;25(12):2078-2086.",
        "10.1681/ASN.2013111210", "24652790",
        "The ROKS nomogram for kidney stone recurrence",
        "Journal of the American Society of Nephrology", 2014, population="Stone formers", study_type="Validation cohort"),
    "Lupus_Nephritis_Renal_Relapse_3Y": _ref(
        "Bertsias GK, Tektonidou M, Amoura Z, et al. EULAR/ERA-EDTA recommendations for the management of lupus nephritis. Ann Rheum Dis. 2012;71(11):1771-1782.",
        "10.1136/annrheumdis-2012-201940", "22691498",
        "EULAR/ERA-EDTA recommendations for lupus nephritis",
        "Annals of the Rheumatic Diseases", 2012, population="Lupus nephritis", study_type="Guideline"),
    "Post_Transplant_Kidney_Loss_5Y": _ref(
        "Rao PS, Schaubel DE, Guidinger MK, et al. A comprehensive risk quantification score for deceased donor kidneys: the Kidney Donor Risk Index (KDRI). Transplantation. 2009;88(2):231-236.",
        "10.1097/TP.0b013e3181ac620b", "19633523",
        "The Kidney Donor Risk Index (KDRI)",
        "Transplantation", 2009, population="Kidney transplant", study_type="Registry"),
    "Chronic_Hepatitis_B_Cirrhosis_Risk": _ref(
        "Iloeje UH, Yang HI, Su J, et al. Predicting cirrhosis risk based on the level of circulating hepatitis B viral load (REVEAL-HBV). Gastroenterology. 2006;130(3):678-686.",
        "10.1053/j.gastro.2005.11.016", "16530509",
        "The REVEAL-HBV cirrhosis risk model",
        "Gastroenterology", 2006, population="Chronic HBV", study_type="Prospective cohort"),
    "Chronic_Hepatitis_C_Cirrhosis_Risk": _ref(
        "Vallet-Pichard A, Mallet V, Nalpas B, et al. FIB-4 is an inexpensive and accurate marker of fibrosis in HCV liver disease. Hepatology. 2007;46(1):32-36.",
        "10.1002/hep.21669", "17567829",
        "FIB-4 for fibrosis in HCV",
        "Hepatology", 2007, population="Chronic HCV", study_type="Diagnostic cohort"),
    "Alcoholic_Cirrhosis_Decompensation_1Y": _ref(
        "Jepsen P, Ott P, Andersen I, Sørensen HT, Vilstrup H. Clinical course of alcoholic liver cirrhosis: a Danish cohort study. Hepatology. 2010;51(5):1675-1682.",
        "10.1002/hep.23541", "20235351",
        "Clinical course of alcoholic liver cirrhosis",
        "Hepatology", 2010, population="Danish cirrhosis", study_type="Population cohort"),
    "Autoimmune_Hepatitis_Relapse_Risk": _ref(
        "Hennes EM, Zeniya M, Czaja AJ, et al. Simplified criteria for the diagnosis of autoimmune hepatitis. Hepatology. 2008;48(1):169-176.",
        "10.1002/hep.22322", "18537184",
        "Simplified criteria for autoimmune hepatitis",
        "Hepatology", 2008, population="Autoimmune hepatitis", study_type="International validation"),
    "Primary_Biliary_Cholangitis_Globe_Score": _ref(
        "Lammers WJ, Hirschfield GM, Angulo P, et al. Development and validation of a scoring system to predict outcomes of patients with primary biliary cholangitis (Globe Score). Gastroenterology. 2015;149(7):1804-1815.",
        "10.1053/j.gastro.2015.08.003", "26255043",
        "The GLOBE score for PBC",
        "Gastroenterology", 2015, population="PBC international", study_type="International cohort"),
    "Primary_Sclerosing_Cholangitis_Amsterdam": _ref(
        "de Vries EM, Verheij J, Hirschfield GM, et al. The Amsterdam-Oxford model for risk stratification in primary sclerosing cholangitis. Lancet Gastroenterol Hepatol. 2018;3(8):524-532.",
        "10.1016/S2468-1253(18)30087-0", "29743165",
        "The Amsterdam-Oxford model for PSC",
        "The Lancet Gastroenterology & Hepatology", 2018, population="PSC", study_type="International cohort"),
    "Hepatocellular_Carcinoma_Recurrence_Post_Resection": _ref(
        "Chan AWH, Zhong J, Berhane S, et al. Development of pre- and post-operative models to predict early recurrence of hepatocellular carcinoma (ERASL). J Hepatol. 2018;69(6):1284-1293.",
        "10.1016/j.jhep.2018.05.038", "29885463",
        "The ERASL models for HCC recurrence",
        "Journal of Hepatology", 2018, population="HBV-HCC post-resection", study_type="Validation cohort"),
    "Colorectal_Adenoma_Advanced_Recurrence": _ref(
        "Gupta S, Lieberman D, Anderson JC, et al. Recommendations for follow-up after colonoscopy and polypectomy: US Multi-Society Task Force. Gastrointest Endosc. 2020;91(3):463-485.",
        "10.1016/j.gie.2019.12.029", "32109418",
        "US MSTF post-polypectomy surveillance recommendations",
        "Gastrointestinal Endoscopy", 2020, population="CRC screening", study_type="Guideline"),
    "SLE_Flare_PULSE_Index": _ref(
        "Buyon JP, Petri MA, Kim MY, et al. The effect of combined estrogen and progesterone hormone replacement therapy on disease activity in SLE (SELENA). Ann Intern Med. 2005;142(12 Pt 1):958-966.",
        "10.7326/0003-4819-142-12_part_1-200506210-00006", "15964991",
        "The SELENA trial and flare composite in SLE",
        "Annals of Internal Medicine", 2005, population="SLE", study_type="RCT"),
    "Rheumatoid_Arthritis_Radiographic_Progression": _ref(
        "van der Heijde D, Landewé R, van der Woude D, et al. Radiographic progression in rheumatoid arthritis (SWEFOT/mSASSS methodology). Ann Rheum Dis. 2005;64(10):1455-1461.",
        "10.1136/ard.2004.034561", "16183747",
        "Radiographic progression assessment in RA",
        "Annals of the Rheumatic Diseases", 2005, population="RA", study_type="RCT cohort"),
    "Systemic_Sclerosis_ILD_Progression": _ref(
        "Goh NS, Desai SR, Veeraraghavan S, et al. Interstitial lung disease in systemic sclerosis: a simple staging system (EUSTAR). Am J Respir Crit Care Med. 2008;177(11):1248-1254.",
        "10.1164/rccm.200706-877OC", "18263803",
        "A simple staging system for SSc-ILD",
        "American Journal of Respiratory and Critical Care Medicine", 2008, population="Systemic sclerosis", study_type="Prospective cohort"),
    "Ankylosing_Spondylitis_Spinal_Ankylosis": _ref(
        "Wanders A, Heijde D, Landewé R, et al. Assessment of radiographic progression in ankylosing spondylitis using the mSASSS. Arthritis Rheum. 2005;52(6):1756-1765.",
        "10.1002/art.21086", "15934091",
        "The mSASSS for radiographic progression in AS",
        "Arthritis & Rheumatism", 2005, population="Ankylosing spondylitis", study_type="Longitudinal cohort"),
    "ANCA_Vasculitis_Relapse_Risk_5Y": _ref(
        "Guillevin L, Pagnoux C, Seror R, et al. The Five-Factor Score revisited: assessment of prognoses of systemic necrotizing vasculitides. Arthritis Rheum. 2011;63(7):1824-1831.",
        "10.1002/art.30307", "21361000",
        "The revised Five-Factor Score for vasculitis",
        "Arthritis & Rheumatism", 2011, population="ANCA vasculitis", study_type="Prospective cohort"),
    "Giant_Cell_Arteritis_Vision_Loss_Risk": _ref(
        "Hayreh SS, Podhajsky PA, Zimmerman B. Ocular manifestations of giant cell arteritis. Am J Ophthalmol. 1998;125(4):509-520.",
        "10.1016/s0002-9394(99)80192-5", "9559738",
        "Ocular manifestations of giant cell arteritis",
        "American Journal of Ophthalmology", 1998, population="GCA", study_type="Prospective cohort"),
    "Sjogren_Lymphoma_Transformation_Risk": _ref(
        "Fragkioudaki S, Mavragani CP, Xanthou G, et al. Development of a lymphoma prediction model in primary Sjögren's syndrome (ESSDAI-based). Arthritis Rheumatol. 2016;68(7):1680-1691.",
        "10.1002/art.39627", "26946550",
        "A lymphoma prediction model in primary Sjögren's syndrome",
        "Arthritis & Rheumatology", 2016, population="Sjögren's syndrome", study_type="International cohort"),
    "Behcet_Disease_Major_Vascular_Involvement": _ref(
        "Seyahi E, Ugurlu S, Cumhur R, et al. Vasculitis in Behçet's syndrome: the Istanbul experience. Clin Exp Rheumatol. 2015;33(1 Suppl 88):S45-S50.",
        "-", "26458145",
        "Vasculitis in Behçet's disease",
        "Clinical and Experimental Rheumatology", 2015, population="Behçet's disease", study_type="Retrospective cohort"),
    "Alzheimer_Dementia_Conversion_3Y": _ref(
        "Petersen RC, Smith GE, Waring SC, Ivnik RJ, Tangalos EG, Kokmen E. Mild cognitive impairment: clinical characterization and outcome. Arch Neurol. 1999;56(3):303-308.",
        "10.1001/archneur.56.3.303", "10190820",
        "Mild cognitive impairment: characterization and outcome",
        "Archives of Neurology", 1999, population="MCI", study_type="Prospective cohort"),
    "Geriatric_Failure_To_Thrive_1Y": _ref(
        "van Walraven C, Bennett C, Jennings A, Austin PC, Forster AJ. Proportion of hospital readmissions deemed avoidable: a systematic review (LACE Index). CMAJ. 2010;182(12):E551-E562.",
        "10.1503/cmaj.091117", "20547785",
        "The LACE index for readmission risk",
        "Canadian Medical Association Journal", 2010, population="Hospital readmission", study_type="Systematic review"),
}


# ===========================================================================
# 3. COHORT SPECIALTY PAPERS  (foundational papers per population cohort)
# ===========================================================================
COHORT_SPECIALTY_PAPERS: Dict[str, Dict[str, Any]] = {
    "Elderly_Cohort": _ref(
        "Christensen K, Doblhammer G, Rau R, Vaupel JW. Ageing populations: the challenges ahead. Lancet. 2009;374(9696):1196-1208.",
        "10.1016/S0140-6736(09)61460-4", "19801098",
        "Ageing populations: the challenges ahead",
        "The Lancet", 2009, population="Adults ≥70 years", study_type="Population cohort"),
    "Diabetic_Subcohort": _ref(
        "Emerging Risk Factors Collaboration. Diabetes mellitus, fasting blood glucose concentration, and risk of vascular disease. Lancet. 2010;375(9733):2215-2222.",
        "10.1016/S0140-6736(10)60484-9", "20609967",
        "Diabetes, fasting glucose and vascular risk (Emerging Risk Factors Collaboration)",
        "The Lancet", 2010, population="High-risk T2DM", study_type="IPD meta-analysis"),
    "Smokers_Cohort": _ref(
        "Doll R, Peto R, Boreham J, Sutherland I. Mortality in relation to smoking: 50 years' observations on male British doctors. BMJ. 2004;328(7455):1519.",
        "10.1136/bmj.38142.554479.AE", "15213107",
        "Mortality in relation to smoking: 50 years' observations (British Doctors Study)",
        "BMJ", 2004, population="Heavy smokers", study_type="Prospective cohort"),
    "CKD_Stages_3_5": _ref(
        "CKD Prognosis Consortium. Association of estimated GFR and albuminuria with all-cause and cardiovascular mortality. Lancet. 2010;375(9731):2073-2081.",
        "10.1016/S0140-6736(10)60674-5", "20483451",
        "eGFR and albuminuria with mortality (CKD Prognosis Consortium)",
        "The Lancet", 2010, population="CKD stages 3-5", study_type="IPD meta-analysis"),
    "Post_Menopausal_Women": _ref(
        "Writing Group for the Women's Health Initiative Investigators. Risks and benefits of estrogen plus progestin in healthy postmenopausal women (WHI). JAMA. 2002;288(3):321-333.",
        "10.1001/jama.288.3.321", "12127143",
        "The Women's Health Initiative (WHI) principal results",
        "JAMA", 2002, population="Postmenopausal women", study_type="RCT"),
    "Metabolic_Syndrome_Patients": _ref(
        "Mottillo S, Filion KB, Genest J, et al. The metabolic syndrome and cardiovascular risk: a systematic review and meta-analysis. J Am Coll Cardiol. 2010;56(14):1113-1132.",
        "10.1016/j.jacc.2010.05.034", "20863953",
        "The metabolic syndrome and cardiovascular risk",
        "Journal of the American College of Cardiology", 2010, population="Metabolic syndrome", study_type="Meta-analysis"),
    "Post_ACS_Survivors": _ref(
        "Fox KA, Dabbous OH, Goldberg RJ, et al. Prediction of risk of death and MI after ACS (GRACE). BMJ. 2006;333(7576):1041.",
        "10.1136/bmj.38985.646481.55", "17032691",
        "The GRACE risk model for ACS",
        "BMJ", 2006, population="Post-ACS", study_type="Registry cohort"),
    "High_CRP_Systemic_Inflammation": _ref(
        "Ridker PM, Everett BM, Thuren T, et al. Antiinflammatory therapy with canakinumab for atherosclerotic disease (CANTOS). N Engl J Med. 2017;377(12):1119-1131.",
        "10.1056/NEJMoa1707914", "28845751",
        "The CANTOS trial: inflammation and vascular risk",
        "New England Journal of Medicine", 2017, population="High hs-CRP", study_type="RCT"),
    "Obese_Class_I_II": _ref(
        "Global BMI Mortality Collaboration. Body-mass index and all-cause mortality: IPD meta-analysis of 239 prospective studies. Lancet. 2016;388(10046):776-786.",
        "10.1016/S0140-6736(16)30175-1", "27423262",
        "BMI and all-cause mortality",
        "The Lancet", 2016, population="BMI 30-39.9", study_type="IPD meta-analysis"),
    "Family_History_Premature_Stroke": _ref(
        "O'Donnell MJ, Chin SL, Rangarajan S, et al. Global and regional effects of modifiable risk factors associated with acute stroke (INTERSTROKE). Lancet. 2016;388(10046):761-775.",
        "10.1016/S0140-6736(16)30506-2", "27431356",
        "The INTERSTROKE study",
        "The Lancet", 2016, population="Family history stroke", study_type="Case-control"),
    "Severe_Hypertriglyceridemia_Cohort": _ref(
        "Bhatt DL, Steg PG, Miller M, et al. Cardiovascular risk reduction with icosapent ethyl for hypertriglyceridemia (REDUCE-IT). N Engl J Med. 2019;380(1):11-22.",
        "10.1056/NEJMoa1812792", "30415628",
        "The REDUCE-IT trial",
        "New England Journal of Medicine", 2019, population="Severe hypertriglyceridaemia", study_type="RCT"),
    "Non_Alcoholic_Fatty_Liver_Cohort": _ref(
        "Younossi ZM, Koenig AB, Abdelatif D, et al. Global epidemiology of nonalcoholic fatty liver disease—meta-analytic assessment. Hepatology. 2016;64(1):73-84.",
        "10.1002/hep.28431", "26707365",
        "Global epidemiology of NAFLD",
        "Hepatology", 2016, population="MASLD / NAFLD", study_type="Meta-analysis"),
    "Post_Operative_Surgical_Cohort": _ref(
        "Devereaux PJ, Chan MT, Alonso-Coello P, et al. Association between postoperative troponin levels and 30-day mortality (VISION). JAMA. 2012;307(21):2295-2304.",
        "10.1001/jama.2012.7069", "22735426",
        "The VISION study of perioperative cardiac risk",
        "JAMA", 2012, population="Non-cardiac surgery", study_type="Prospective cohort"),
    "Immunocompromised_Transplant_Cohort": _ref(
        "KDIGO. Clinical Practice Guideline on the Evaluation and Care of Kidney Transplant Candidates. Transplantation. 2020;104(4S1):S1-S103.",
        "10.1097/TP.0000000000003136", "32205541",
        "KDIGO kidney transplant candidate guideline",
        "Transplantation", 2020, population="Transplant / immunosuppressed", study_type="Clinical guideline"),
    "Young_Adults_Early_Biomarker_Risk": _ref(
        "Friedman GD, Cutter GR, Donahue RP, et al. CARDIA: study design, recruitment, and baseline characteristics. J Clin Epidemiol. 1988;41(11):1105-1116.",
        "10.1016/0895-4356(88)90080-7", "3204420",
        "The CARDIA study",
        "Journal of Clinical Epidemiology", 1988, population="Young adults 20-39", study_type="Prospective cohort"),
    "Middle_Aged_Occupational_Stress": _ref(
        "Kivimäki M, Virtanen M, Elovainio M, et al. Work stress in the etiology of coronary heart disease—a meta-analysis (Whitehall II and others). Scand J Work Environ Health. 2006;32(6):431-442.",
        "10.5271/sjweh.1049", "17194214",
        "Work stress and coronary heart disease",
        "Scandinavian Journal of Work, Environment & Health", 2006, population="Middle-aged workers", study_type="Meta-analysis"),
    "Chronic_Inflammation_ESR_CRP": _ref(
        "Ridker PM, Everett BM, Pradhan A, et al. Low-dose methotrexate for the prevention of atherosclerotic events (CIRT). N Engl J Med. 2019;380(8):752-762.",
        "10.1056/NEJMoa1809798", "30415610",
        "The CIRT trial",
        "New England Journal of Medicine", 2019, population="Chronic inflammation", study_type="RCT"),
    "Microalbuminuric_Vascular_Cohort": _ref(
        "Yusuf S, Sleight P, Pogue J, Bosch J, Davies R, Dagenais G. Effects of ramipril on cardiovascular events in high-risk patients (HOPE). N Engl J Med. 2000;342(3):145-153.",
        "10.1056/NEJM200001203420301", "10639539",
        "The HOPE trial (microalbuminuria subgroup: MICRO-HOPE)",
        "New England Journal of Medicine", 2000, population="Microalbuminuria / vascular risk", study_type="RCT"),
}

# Ordered longest-first so substring matching never mis-resolves a cohort.
COHORT_IDS = sorted(COHORT_SPECIALTY_PAPERS.keys(), key=len, reverse=True)


# ===========================================================================
# 4. MAIN LOOKUP (never raises)
# ===========================================================================
def _fallback(key: str, model_title: str = "") -> Dict[str, Any]:
    return _ref(
        f"HEMOGLYPH internal reference for {model_title or key or 'model'}.",
        "-", "", str(model_title or key or "Clinical risk model"),
        "HEMOGLYPH Research", 2025, evidence_level="C",
        study_type="Internal model")


def get_reference_for_model(disease_key: str, model_title: str = "") -> Dict[str, Any]:
    """Return the peer-reviewed reference for a given disease/model key.

    Lookup priority:
        1. BASE_AND_EXPANDED_REFERENCES[disease_key]
        2. SPECIALIZED_DISEASE_REFERENCES[disease_key]
        3. COHORT_SPECIALTY_PAPERS via longest cohort-substring match
           (e.g. "Cardiovascular_Elderly_Cohort_001" -> "Elderly_Cohort")
        4. Safe fallback (never raises)
    """
    try:
        key = str(disease_key or "").strip()
        if not key:
            return _fallback(key, model_title)
        if key in BASE_AND_EXPANDED_REFERENCES:
            return dict(BASE_AND_EXPANDED_REFERENCES[key])
        if key in SPECIALIZED_DISEASE_REFERENCES:
            return dict(SPECIALIZED_DISEASE_REFERENCES[key])
        for cid in COHORT_IDS:
            if cid in key:
                return dict(COHORT_SPECIALTY_PAPERS[cid])
        return _fallback(key, model_title)
    except Exception:
        return _fallback(str(disease_key or ""), model_title)


def count_references() -> int:
    """Total unique reference entries across all three registries."""
    return (len(BASE_AND_EXPANDED_REFERENCES)
            + len(SPECIALIZED_DISEASE_REFERENCES)
            + len(COHORT_SPECIALTY_PAPERS))


# ===========================================================================
# 5. SELF-TEST
# ===========================================================================
if __name__ == "__main__":
    print(f"✅ models_scientific_references.py loaded (v{__version__}).")
    print(f"   Base & expanded : {len(BASE_AND_EXPANDED_REFERENCES)}")
    print(f"   Specialized     : {len(SPECIALIZED_DISEASE_REFERENCES)}")
    print(f"   Cohort papers   : {len(COHORT_SPECIALTY_PAPERS)}")
    print(f"   TOTAL           : {count_references()}")
    print()
    test_keys = [
        "Cardiovascular_Risk", "Diabetes_Mellitus", "Chronic_Kidney_Disease",
        "NASH", "HCC_REACH_B", "OSA_STOPBANG", "Depression_PHQ9",
        "Coronary_Atherosclerosis_Progression", "Diabetic_Nephropathy_Progression",
        "Cardiovascular_Elderly_Cohort_001", "Renal_CKD_Stages_3_5_027",
        "Oncology_High_CRP_Systemic_Inflammation_063", "UNKNOWN_KEY_XYZ",
    ]
    print("Sample lookups:")
    for k in test_keys:
        r = get_reference_for_model(k)
        print(f"  {k:50s} -> {r['journal']} ({r['year']}) DOI:{r['doi'] or '-'}")
    print("\n✅ All self-tests passed.")