# Step 5 validation: AI vs hand-labelled golden set

Items compared: **24**

| Field | Agreement |
|---|---|
| is_relevant | **79%** (19/24) |
| lifecycle_stage | **83%** (15/18) |
| action | **39%** (7/18) |
| trigger | **78%** (14/18) |
| segment invented by AI | 6 of 24 items |

## Disagreements (failure cases)

| uid | field | human | AI |
|---|---|---|---|
| tr_00827 | action | unknown | checking |
| tr_00827 | trigger | setup_friction | none |
| yo_01800 | lifecycle_stage | unknown | pre_start |
| yo_01800 | action | unknown | started |
| tr_00891 | action | unknown | continued |
| yo_01987 | action | considering_stop | restarted |
| tr_01080 | is_relevant | no | yes |
| pl_00133 | action | checking | continued |
| pl_00292 | action | lapsed_involuntary | continued |
| pl_00292 | trigger | payment_failure | app_trust_issue |
| ap_00022 | is_relevant | no | yes |
| pl_00180 | is_relevant | no | yes |
| yo_02094 | is_relevant | no | yes |
| yo_01757 | action | unknown | started |
| yo_01842 | action | unknown | started |
| tr_01336 | lifecycle_stage | unknown | m12_plus |
| tr_01336 | trigger | none | negative_returns |
| tr_01393 | action | paused | restarted |
| tr_01393 | trigger | other | none |
| pl_00070 | is_relevant | no | yes |
| pl_00148 | lifecycle_stage | unknown | pre_start |
| pl_00148 | action | lapsed_involuntary | setup_failed |
| pl_00373 | action | lapsed_involuntary | setup_failed |

## Trigger confusion (human → AI)

- none → negative_returns: 1
- other → none: 1
- payment_failure → app_trust_issue: 1
- setup_friction → none: 1