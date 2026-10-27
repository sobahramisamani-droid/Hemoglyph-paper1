# Activity-guided provenance repair — protocol (Phase A frozen before any activity count was computed)

Date: 2026-10-27. Registry: 14.2.0 (shipped with engine v8.2; 33,183 executable rules, 272 curated anchors).

## Problem
The frozen concordance audit (Note 8) found 92 % of sampled rules unresolvable from their locators. Ablation
shows the engine's result rests on the anchors and the syndrome layer, with the 33k bulk adding 1-3 points.
Auditing 33k rules uniformly is neither feasible nor useful. This protocol directs audit and re-sourcing effort
to the rules that actually act, using only label-free execution logs.

## Phase A — activity log (label-free)
Run the engine on real panels and record, per executable rule and per corpus:
  fired        = interpretation status in {criterion_met, possible_pattern, screening_positive,
                 compatible_pattern, urgent_pattern} for that case;
  contrib10    = fired AND the rule's disease_id is in the case's differential top-10;
  contrib5     = fired AND disease_id in top-5.
Corpora (all already in the workspace; no labels are read): eICU-CRD demo 2,314 first panels (encounter = icu,
the benchmark setting); NHANES 2017-18 random 1,000 adults (seed 20261027; encounter = community);
NHANES 2015-16 random 500 adults (same seed). Counts are written as one compressed table; no per-case output.

## Definitions (fixed now)
  ACTIVE CORE  = executable rules with contrib10 >= 1 in any corpus.
  HOT CORE     = contrib10 >= 10 cases pooled.
  DORMANT      = executable rules that never fired in any corpus.
  Reported with denominators: n rules, share of 33,183, share of anchors in each class, provenance class of each
  class using the same locator classifier as Fig. S1 (DOI resolved / landing page / URL only / unreachable / none).

## Phase B — re-sourcing of the active core (no rule logic is changed)
For each ACTIVE CORE rule, in order of contrib10: open the cited source from the sandbox; if the source text
contains the rule's threshold for the rule's analyte, record a section/table-level locator and the verbatim
sentence; if the source is reachable and does not contain it, record "not_in_source"; if unreachable, record
"unreachable". New locators are stored in a separate file (`core_locators.json`), never by editing thresholds.
Rules whose source is reachable but does not contain the statement are listed as discordance candidates for the
first author; nothing is retired automatically in this phase.

## Phase C — fresh one-shot concordance sample
After Phase B, 100 rules are drawn from the ACTIVE CORE (seed 20261028, by sorted rule_id) and rated once under
the Note 8 protocol (same labels, same tie-break, single AI rater, verbatim quotation mandatory for every
non-UNRESOLVABLE verdict). Results are reported next to the Note 8 bulk figures with both denominators. Rules
already in the Note 8 sample are excluded from the draw.

## Registered expectations (not targets)
ACTIVE CORE between 800 and 4,000 rules; anchors over-represented in the HOT CORE (>= 30 % of hot-core rules
anchors although anchors are 0.8 % of rules); Phase B reachable-with-statement share for the core 30-60 %;
Phase C unresolvable share below the Note 8 figure (92 %). Whatever is found is reported.

## Not done
No threshold, weight or status is changed on the basis of activity or concordance in this work; frozen v7 and
registry 14.1.0 results stand. Candidate changes go to release 15 with their own one-shot gate.
