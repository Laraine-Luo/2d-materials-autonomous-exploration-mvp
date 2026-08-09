# 初赛PDF第二至第四部分草案（由MVP实现反推）

> 本文不修改已经冻结的第一部分。方括号中的仓库证据路径用于写作和评审追踪，正式排版时可缩写为脚注、二维码或仓库链接。

## 二、环境接口

### 2.1 固定规则

本项目将探索环境限定为一个固定二维材料候选池上的有限预算序贯搜索任务。正式研究数据仅来自Materials Project；160条随机合成记录只用于验证软件闭环，不参与科学评价。候选以Materials Project ID作为唯一身份，化学式只用于分组。以MoS2为例，其索引路径为`Materials Explorer → Mo–S → MoS2 → mp-id`，同一化学式下网页检索得到12条不同结构记录，不能合并为一个候选。[证据：`docs/mos2-materials-project-index-catalog.md`]

一次正式运行冻结数据库版本、计算方法队列、候选池、目标区间、初始已知样本、查询预算与随机种子。Band Gap目标区间暂设为1.5—2.5 eV；Formation Energy为主要稳定性条件，Energy Above Hull与Materials Project的`is_stable`标志为辅助条件：

\[
S(x)=\mathbf 1[E_f(x)\le-0.2]\land
\mathbf 1[E_{hull}(x)\le0.1\lor is\_stable(x)].
\]

这些阈值是MVP预注册评价规则，不等同于普遍可合成判据。真实数据中只评价Materials Project返回值，不用简单函数生成或校正性质；人工性质函数仅存在于随机测试夹具中。公式层网页记录、二维性不确定记录、方法缺失记录和跨版本记录均默认隔离。[证据：`config.json`、`config/materials_project_mapping_list.json`、`config/formal_record_promotion_rules.json`]

首个正式展示队列为`MP-MoS2 Polymorph Demo v1`。12条公式层索引经MP API、身份、二维性与方法审核后有9条审计合格，其中7条同时通过固定稳定性门槛。原4＋4方案因稳定候选不足而失败关闭；在查看任何有效策略结果前，预算预注册修订为3条初始标签、3次单条查询，并保留1条未揭示候选。该队列只用于真实数据映射、审核和最小闭环展示，不用于证明策略优越性。[证据：`config/first_formal_queue.json`、`docs/run-37-budget-preregistration.md`]

### 2.2 观察／行动／反馈

Agent每轮观察包括：剩余候选的MP ID与结构特征、当前Band Gap预测均值、Bootstrap模型离散度、稳定性资格、历史已查询记录、剩余预算和人工审核状态。任何`uncertain_2d`或方法未确认记录只进入审核与偏离统计，不进入训练集。

Agent的核心行动是从合格候选池选择下一条MP ID进行查询。MVP提供三种可替换策略：Random从剩余候选均匀抽样；Static Top-N使用初始模型冻结排序；Iterative在每轮反馈后重训模型，并最大化

\[
A(x)=(1-w)T(\hat E_g(x))+w\frac{u(x)}{\max_{x'}u(x')},\quad w=0.35,
\]

其中`T`表示预测值对目标Band Gap区间的接近度，`u`为12个Bootstrap岭回归模型的预测离散度。该策略是“目标利用＋不确定性探索”的简化函数，不称为尚未实现的Expected Improvement或UCB。

环境在每次查询后揭示数据库Band Gap及稳定性字段，消耗一次预算，计算误差与发现信号，写入历史并在Iterative策略下更新模型。反馈是数据库计算代理值而非实验真值。[证据：`src/materials_mvp/environment.py`、`model.py`、`signal.py`]

### 2.3 记录与预算

每轮日志至少保存：轮次、策略、MP ID、预测Band Gap、不确定性、数据库Band Gap、Formation Energy、Energy Above Hull、`is_stable`、二维性状态、选择理由、绝对误差、目标命中、发现等级、规则版本、人工复核标志与预算位置。探索状态字段统一采用`exploration_status_`前缀。

正式微型队列的查询预算为3，批量大小为1；7条稳定记录中3条作为共同初始集、每种策略查询3条、保留1条未揭示。若稳定候选少于7条则运行失败关闭。API请求、字段映射、护照更新和失败原因分别保存审计。原始API响应与密钥只存放在Git忽略目录，公开仓库只保留脱敏状态与统计。[证据：`artifacts/formal_queue_pipeline_status.json`、`formal_closed_loop_summary.json`、`docs/mos2-passport-readiness.md`]

## 三、发现信号与参照

### 3.1 什么算发现

本项目将“查询命中”与“科学发现”分层：D0为可追踪的技术／索引事件；D1为数据库Band Gap落入预注册区间；D2为D1同时通过MP身份、二维性、稳定性、计算方法与字段质量审核；D3为候选、规律、异常或负结果在留出数据和重复运行中稳定复现；D4为更高精度计算、独立数据、文献或实验外部验证。初赛MVP不宣称D4，单条查询最高只能自动判定D2。[证据：`docs/discovery-signal-spec-3.1.md`]

异常信号预定义为

\[
|\hat E_g-E_g|>\max(0.6\,\mathrm{eV},2u),
\]

触发后进入人工审核，未经确认不回流训练。负发现包括：Iterative在重复实验中未超过基线；目标Band Gap与稳定性长期冲突；高不确定性采样未提高有效候选率；某结构区域达到预设样本量后仍无合格候选；或二维性、方法和字段缺失导致原问题边界必须收缩。每条信号保存规则版本、材料身份、预算位置、触发原因和审核结论。

### 3.2 平凡解／随机／无干预

参照包括：Random表示随机运气；Static Top-N表示一次预测后静态排序、反馈不重训；Iterative表示预测—选择—反馈—更新闭环。三者共享相同候选池、初始样本、预算、稳定性函数和目标区间。比较指标为D2数量、D2命中率、首次D2所需预算、Band Gap MAE、稳定性违规数和异常率。

正式MP 3＋3＋1单次微型试跑中三种策略均得到2个D2，只证明闭环可运行。随后按预注册的20个共同种子重复比较，Random、Static Top-N和Iterative平均D2分别为1.45、2.00和1.75；平均命中率为48.33%、66.67%和58.34%。Iterative相对Random的配对差异为+0.30，95% Bootstrap区间[0.05, 0.55]；相对Static Top-N为-0.25，区间[-0.45, -0.05]。Iterative超过Random但未超过Static Top-N，形成当前固定环境内的D3负向策略信号。事后机制检查显示，Static在20次运行中始终先查询两个目标候选并始终避开`mp-1018809`；Iterative则20/20次查询该非目标记录，且平均选择不确定性更高。该观察只生成“微型池中探索机会成本”的待检验假设，不作为因果结论。[证据：`artifacts/formal_repeated_evaluation_summary.json`、`formal_material_selection_frequency.csv`]

### 3.3 最低成功与失败标准

技术最低成功为：固定配置下一键完成采集／映射／查询闭环，预算正确终止，日志字段完整，随机种子可复现。真实微型队列技术最低成功为至少7条记录通过API、二维性、方法、字段及稳定性审核，并完成3＋3＋1闭环。策略正向D3要求至少20个预注册共同种子下，Iterative平均D2同时高于两条基线至少10%，且两组成对95%区间下界均大于0；负向D3要求相对至少一条必需基线的区间上界低于10%最低有意义增益。本轮正向门槛失败、负向门槛通过。

以下情况判定失败而非事后调整成功标准：API或字段映射无法复现；训练／反馈泄漏；正式稳定候选少于7条；稳定性违规；不同数据库版本或计算方法被混合；Iterative未超过基线；或结果仅由个别离群点驱动。失败后保留完整证据，并据此缩小候选范围、修正字段、目标区间或审核规则。

## 四、最小验证计划

### 4.1 一次试跑怎么做

输入为固定版本Materials Project中MoS2公式层的12条MP ID。首先通过官方`mp-api`请求Summary字段，保存原始响应至本地忽略目录并生成脱敏API审计；随后按mapping list映射字段，为每个MP ID生成证据护照，人工审核二维性及`origins → task_id → thermo run_type`方法链。对7条最终稳定合格记录，以不读取Band Gap标签的结构最远点采样固定3条共同初始样本，采用3次查询预算依次运行Random、Static Top-N与Iterative，并为每种策略保留1条未揭示候选，输出逐轮日志、策略汇总、D0—D2信号及失败记录。

正式API采集后，首次4＋4试跑因运行器未重复施加稳定性门槛而整体作废。修正后，在任何有效结果产生前预注册3＋3＋1边界并完成合法闭环；再在查看重复结果前冻结20个共同种子、10,000次配对Bootstrap及D3门槛。最终三种策略完成60条策略运行记录，无稳定性违规，Iterative未达到预注册的双基线优势。[证据：`artifacts/invalid_run36_invalidation.json`、`docs/run-37-budget-preregistration.md`、`docs/run-38-repeated-evaluation-preregistration.md`、`artifacts/formal_repeated_evaluation_summary.json`]

为检验该负向信号能否跨出MoS2微型池，本项目在查询前冻结Mo/W与S/Se/Te组成的六个MX2公式族。官方API从同一数据库版本返回44个唯一MP ID，其中MoS2的12条只作开发／漂移对照，其余五族32条作为独立公式来源；25条通过组合稳定性预筛，但全部仍处于二维性和方法未审核的索引隔离态。[证据：`artifacts/mp_mx2_validation_index_audit.json`、`docs/mp-mx2-validation-index-catalog.md`]

随后在不读取Band Gap的条件下冻结25个结构审核ID。API返回25/25结构与来源，身份完全匹配；Larsen/Gorai一致支持2D 13条，另12条为Larsen及全部结构分量支持2D、Gorai判1D，Robocrystallographer对12/12均描述为二维。方法链25/25可解析，其中24条属于统一`GGA/NSCF Line`队列，`mp-1120746`为`r2SCAN/Structure Optimization`注意项。当前仅形成24条待人工签署的验证资格建议，无记录被自动晋级。[证据：`artifacts/mp_mx2_structure_response_audit.json`、`mp_mx2_method_robocrys_evidence_audit.json`、`docs/mp-mx2-combined-review-proposal.md`]

项目所有者随后签署24＋1决定：24条获得独立验证候选资格，`mp-1120746`继续隔离，获准训练为0条。Agent观察接口仅包含身份、结构特征和稳定性信息，不含Band Gap；标签保存在Git忽略的oracle文件中，仅能在查询后由环境揭示，公开护照只保存标签承诺哈希。[证据：`artifacts/mp_mx2_human_review_decision_audit.json`、`mx2_validation_agent_observations.csv`、`docs/run-42-human-decision-and-label-isolation.md`]

在查看验证标签前，项目冻结8次顺序查询、20个共同种子、Random和Static Top-N两条必需基线，以及唯一主策略`Iterative w=0.35`。正式结果中，主策略平均获得3.40个D2，高于Random的2.60（差异+0.80，95%区间[0.10,1.60]），但低于Static的3.85（差异-0.45，区间[-0.90,0.00]），因此未达到同时超过两条基线的正向门槛，登记为限定于该MX2队列的D3负向策略信号。诊断策略`w=0.15`平均4.70个D2，但依据防事后挑选规则不能替换主策略，只形成下一独立队列的待检验假设。[证据：`config/mx2_cross_formula_validation_v1.json`、`artifacts/mx2_cross_formula_validation_summary.json`、`docs/run-43-cross-formula-validation-result.md`]

### 4.2 主要风险与失败路径

| 风险 | 检测 | 处理与保留证据 |
|---|---|---|
| API／网络失败 | 响应状态、HTTP／DNS错误 | 停止映射；保存失败审计，不替代数据 |
| 数据版本漂移 | 一次采集出现多个／缺失版本 | 整批隔离并重新冻结版本 |
| 计算方法混合 | `origins`与Thermo `run_type` | 方法缺失或不一致进入审核队列 |
| 非二维结构混入 | MP ID级结构、页面描述、人工审核 | `uncertain_2d`只统计不训练 |
| Band Gap代理误差 | 异常阈值、留出误差、方法记录 | 标记异常，不直接回流训练 |
| 训练／反馈泄漏 | 隐藏标签检查、日志回放 | 该轮评价作废并修正切分 |
| 小样本偶然性 | 多种子、成对置信区间 | 不满足门槛则报告未超过参照 |
| LLM或人工无证据批准 | 审核者、时间、理由和证据必填 | 晋级失败，保留阻塞原因 |

### 4.3 复现与开源计划

仓库公开环境代码、映射list、固定配置、三策略、发现规则、自动测试、索引清单、证据护照、审计状态和运行说明。合成夹具明确标注为无科学依据的测试数据。Materials Project数据注明数据库版本、查询条件和CC BY 4.0许可；API密钥、账号、原始本地响应和虚拟环境不上传。正式API使用固定`mp-api==0.46.4`与Python 3.11+，所有公开包执行秘密扫描。进入复赛后提供一键入口、随机种子、多次运行日志和基线结果，使其他团队能够替换策略而复用同一环境与评价规则。

Materials Project API与字段使用依据：

1. https://docs.materialsproject.org/downloading-data/using-the-api
2. https://docs.materialsproject.org/downloading-data/using-the-api/querying-data
3. https://docs.materialsproject.org/downloading-data/using-the-api/examples
4. https://docs.materialsproject.org/methodology/materials-methodology/electronic-structure
