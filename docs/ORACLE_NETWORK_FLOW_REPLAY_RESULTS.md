# ORACLE Network Flow Replay Results

Rows were replayed one by one as deterministic flow events. These are dataset replay simulations, not live packet capture.

| Path | Events | Success | Degraded | Failed | Throughput events/sec | p95 ms | Audit Rate | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CIC production FusionEngine | 40 | 40 | 0 | 0 | 1.54 | 68.9458 | 1.0 | 0.3 | 0.4615 |
| UNSW mapped production path | 40 | 40 | 0 | 0 | 3.54 | 85.861 | 1.0 | 0.0 | 0.0 |
| CSE production FusionEngine | 40 | 40 | 0 | 0 | 3.26 | 74.603 | 1.0 | 0.0 | 0.0 |
| CSE repair candidate | 40 | 40 | 0 | 0 | 9.24 | 124.0604 | 1.0 | 0.9 | 0.9474 |
| DoHBrw mapped production path | 40 | 40 | 0 | 0 | 2.91 | 352.6218 | 1.0 | 0.0 | 0.0 |
| DoHBrw native adapter | 40 | 40 | 0 | 0 | 4.02 | 128.5997 | 1.0 | 1.0 | 0.9524 |
