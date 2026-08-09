# 首个正式MoS2队列：合并人工审核表

> 自动证据建议达到门槛，不等于正式队列已经获批。人工二维性与方法结论仍需签署。

| MP ID | 二维性建议 | 方法建议 | 建议入队 | 人工二维性 | 人工方法 | 最终资格 |
|---|---|---|---:|---|---|---:|
| `mp-1434` | recommended_confirmed_2d | recommended_pass | True | pending | pending | False |
| `mp-2815` | recommended_confirmed_2d | recommended_pass | True | pending | pending | False |
| `mp-1018809` | recommended_confirmed_2d | recommended_pass | True | pending | pending | False |
| `mp-1027525` | recommended_confirmed_2d | recommended_pass | True | pending | pending | False |
| `mp-1025874` | recommended_confirmed_2d | recommended_pass | True | pending | pending | False |
| `mp-1023939` | recommended_confirmed_2d | recommended_pass | True | pending | pending | False |
| `mp-1023924` | recommended_confirmed_2d | recommended_pass | True | pending | pending | False |
| `mp-990083` | non_2d | attention_required | False | pending | pending | False |
| `mp-1405065` | non_2d | attention_required | False | pending | pending | False |
| `mp-558544` | recommended_confirmed_2d | recommended_pass | True | pending | pending | False |
| `mp-1238797` | recommended_confirmed_2d | recommended_pass | True | pending | pending | False |
| `mp-1042086` | non_2d | recommended_pass | False | pending | pending | False |

## 队列判定

- 自动证据建议入队：9条；
- 人工签署入队：0条；
- 正式闭环最低门槛：8条；
- 当前结论：建议数量达到门槛，但正式闭环仍被人工审核闸门阻断。

## 结果说明

合并证据建议9条记录进入正式微型队列，3条作为非二维/方法异常反例保留。其中三条多层结构记录保留Gorai=1的失败证据，不以最终建议覆盖原始异常。在人工结论签署前，所有记录的最终训练资格仍为False。
