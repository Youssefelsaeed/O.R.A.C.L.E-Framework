# ORACLE Feature Mapping And Generalization

| Dataset | Class | Mean schema score | Production path valid | Candidate/adapter required |
| --- | --- | ---: | --- | --- |
| CIC-IDS2017 | IN_DOMAIN | 1.0 | True | False |
| UNSW-NB15 | WEAK_SCHEMA_GENERALIZATION | 0.5 | False | False |
| CSE-CIC-IDS2018 | PARTIAL_GENERALIZATION | 0.9872 | True | True |
| DoHBrw | ADAPTER_REQUIRED | 0.0 | False | True |

CIC is the in-domain path. CSE is partial generalization and benefits from the repair candidate. UNSW is weak mapped-schema generalization. DoHBrw requires the native adapter.
