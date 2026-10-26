# B7 — critical-value detection on 50 real eICU-demo stays (25 with >= 1 CAP-critical value) + engine determinism

| | LLM (Arena agent, blind) | Hemoglyph critical_alerts |
|---|---|---|
| Stays with any critical value flagged | 25/25 | 25/25 |
| Individual critical values flagged | 39/39 | 39/39 |
| Stays without a CAP-critical value that were nonetheless flagged (engine: 'CRITICAL VALUE' alert; LLM: any value listed) | 8/25 | 10/25 |

Engine determinism: 3 repeated runs per stay, identical top-10 + alerts in 50/50 stays.

Engine misses: 

LLM misses: 

Engine flags on non-critical stays: 351524: ['hemoglobin = 7.6 g/dL exceeds panic threshol']; 2594608: ['hemoglobin = 7.5 g/dL exceeds panic threshol', 'glucose = 469 mg/dL exceeds panic threshold ']; 2703113: ['troponin_i = 2.44 ng/mL exceeds panic thresh']; 207393: ['troponin_i = 6.67 ng/mL exceeds panic thresh']; 1111554: ['troponin_i = 7.79 ng/mL exceeds panic thresh']; 2742035: ['albumin = 1.7 g/dL exceeds panic threshold (']; 2682904: ['troponin_i = 0.11 ng/mL exceeds panic thresh']; 3088802: ['glucose = 454 mg/dL exceeds panic threshold ', 'bicarbonate = 10 mmol/L exceeds panic thresh']; 2518855: ['bicarbonate = 44 mmol/L exceeds panic thresh']; 893771: ['troponin_i = 0.51 ng/mL exceeds panic thresh']

Note: engine 'false alarms' on non-critical stays are alerts for values outside the CAP list used here (engine panic limits are tighter, e.g. Hb < 8, troponin, glucose > 400) — listed for transparency; the engine also flagged INR 5.7 through the accompanying PT 59.8 s (PT not shown on the blind panel).
