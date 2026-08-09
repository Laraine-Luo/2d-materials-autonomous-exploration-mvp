# Materials Project索引层级记录：MoS2

## 本次网页核验到的层级

Materials Project网页面包屑为：

`Home > Apps > Materials Explorer > Mo–S > MoS2 > mp-1434`

据此，本项目在报告与演示中采用以下索引说明：

| 层级 | 含义 | MoS2示例 |
|---|---|---|
| L0 | 数据库及版本 | Materials Project，网页核验版本`v2026.04.13` |
| L1 | 检索应用 | Materials Explorer |
| L2 | 化学体系层 | `Mo–S` |
| **L3** | **化学式/组成层** | **`MoS2`；本次调用所处层级** |
| L4 | 具体材料结构/多型记录层 | `mp-1434`及同化学式下其他MP ID |
| L5 | 性质与计算记录层 | Band Gap、Formation Energy、Energy Above Hull、计算方法等 |

因此，最终呈现中的标准写法为：

> Materials Project索引路径：Materials Explorer → `Mo–S`化学体系层 → `MoS2`化学式/组成层 → `mp-1434`具体结构记录层。

## 对环境设计的含义

`MoS2`是化学式/组成层，不是唯一候选标识。网页公式查询返回12条不同结构记录，因此探索日志、候选选择和发现信号必须以`material_id`（如`mp-1434`）作为候选主键，并把formula保留为分组与解释字段。不能把同一化学式下的不同结构多型合并为一条材料，也不能仅凭公式层结果宣称发现。

该层级是Materials Project网页检索界面的索引记录；正式批量获取仍应使用官方API，并另行记录API字段、数据库版本和查询条件。
