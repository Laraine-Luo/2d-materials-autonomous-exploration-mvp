# 第6次运行：测试夹具隔离与Materials Project真实网页演练

## 测试数据隔离

160条随机测试记录已迁移至`data/test_fixture/random_synthetic_materials.csv`。目录README明确声明其行数、特征范围、Band Gap和稳定性关系均无经验或文献依据，只用于软件闭环测试。真实Materials Project记录不得写入该目录。

绘图和制表需求已登记到`docs/deferred-figures-and-tables.md`，本轮不实现。

## Materials Explorer实际查询

在已登录Materials Project网站中使用Materials Explorer查询公式`MoS2`，数据库版本为`v2026.04.13`。网页返回12条多型记录，表格字段包含Material ID、晶系、空间群、位点数、Energy Above Hull和Band Gap。

结果显示同一化学式不能直接当作同一候选：12条记录的Energy Above Hull从0到0.65 eV/atom，Band Gap从0到1.66 eV，且晶系/空间群不同。这为“候选单位必须是结构记录/Material ID，而不是只按化学式”提供了真实证据。

## 单条详情核查：mp-1434

人工读取页面得到：

- Formula：MoS2；
- Band Gap：1.38 eV；
- Predicted Formation Energy：−0.966 eV/atom；
- Energy Above Hull：0.000 eV/atom；
- Predicted Stable：是；
- Calculation method：R2SCAN；
- Experimentally Observed：是；
- 页面维度字段：`2D or Layered`；
- 自动描述明确称结构为two-dimensional并由MoS2 sheets组成。

该记录证明三稳定性指标、Band Gap和二维性证据可在真实材料页面中同时核对。但当前数据来自人工网页转录而不是可复现API管线，因此`training_eligible=False`，只作为字段和审计流程演练。

## 运行结果说明

本轮能支持：测试数据与真实数据已物理隔离；Materials Explorer确实提供项目所需的核心性质；同一化学式存在多结构/多性能，候选主键应为Material ID；二维性可由页面字段和自动描述交叉确认。

本轮不能支持：API字段映射已经跑通；全部MoS2记录均为二维；mp-1434可以直接加入训练集；网页转录可替代批量API；单条记录足以验证搜索策略。

## PDF映射

- §2.1：真实候选的身份以Material ID/结构为准，固定数据库版本；
- §2.2：观察包含三稳定性字段、Band Gap、维度证据和计算方法；
- §2.3：保存来源URL、获取日期、数据库版本和训练资格；
- §3.1：二维性与稳定性均经确认后才能形成候选发现信号；
- §4.1：形成一次真实网页字段核查；
- §4.2：网页转录不可扩展、同化学式多型和API未贯通是风险；
- §4.3：最终改为官方API获取并保存许可与引用信息。

