# MoS2二维性人工审核表

> Larsen/CrystalNN 与 Gorai 双算法只提供审核建议；人工结论为 pending 时，一律不得进入训练。

| MP ID | Larsen | Gorai | 结构分量 | 建议状态 | 原因 | 人工结论 |
|---|---:|---:|---|---|---|---|
| `mp-1434` | 2 | 2 | 2 | confirmed_2d | two_algorithm_consensus | pending |
| `mp-2815` | 2 | 2 | 2,2 | confirmed_2d | two_algorithm_consensus | pending |
| `mp-1018809` | 2 | 2 | 2,2 | confirmed_2d | two_algorithm_consensus | pending |
| `mp-1027525` | 2 | 1 | 2,2,2,2 | uncertain_2d | algorithm_disagreement | pending |
| `mp-1025874` | 2 | 1 | 2,2,2 | uncertain_2d | algorithm_disagreement | pending |
| `mp-1023939` | 2 | 1 | 2,2 | uncertain_2d | algorithm_disagreement | pending |
| `mp-1023924` | 2 | 2 | 2 | confirmed_2d | two_algorithm_consensus | pending |
| `mp-990083` | 1 | 1 | 1,1 | non_2d | two_algorithm_non_2d | pending |
| `mp-1405065` | 3 | 3 | 3 | non_2d | two_algorithm_non_2d | pending |
| `mp-558544` | 2 | 2 | 2 | confirmed_2d | two_algorithm_consensus | pending |
| `mp-1238797` | 2 | 2 | 2 | confirmed_2d | two_algorithm_consensus | pending |
| `mp-1042086` | 3 | 3 | 3 | non_2d | two_algorithm_non_2d | pending |

## 队列影响

- 双算法一致支持2D：6条；
- 算法分歧、不确定：3条；
- 双算法不支持2D：3条；
- 正式闭环最低门槛：8条；
- 当前自动证据不足以启动正式闭环。

## 结果说明

双算法将候选分成一致2D、算法分歧和非2D三类。分歧记录继续出现在审核和偏离统计中，但未经人工确认不进入训练。该结果说明二维性闸门能够发现公式级MoS2候选池中的结构差异；不代表6条建议记录已完成人工确认。
