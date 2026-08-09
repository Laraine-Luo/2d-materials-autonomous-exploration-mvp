# 初赛PDF—仓库证据索引（提交版）

本页是四页PDF与公开仓库之间的审计入口。第一部分文字来自已冻结稿，未因结果调整研究问题；第二至第四部分由实际环境、预注册协议和运行结果反推。

| PDF部分 | 评委要确认的事项 | 仓库中的直接证据 | 当前状态 |
|---|---|---|---|
| 1.1 真实问题 | 研究对象不是玩具问题 | `docs/references.md`；`docs/pdf-part1-frozen.md` | 已冻结 |
| 1.2 尚未结构化 | 结构化的是环境、预算、反馈和评价，而非声称主动学习无人研究 | `src/materials_mvp/environment.py`；`config/mx2_cross_formula_validation_v1.json` | 已实现 |
| 1.3 价值与切片 | 固定池、Band Gap、稳定性和有限预算 | `config.json`；Run 43预注册 | 已收缩 |
| 2.1 固定规则 | 单一MP数据源、版本、阈值、隔离规则 | `config/materials_project_mapping_list.json`；`artifacts/mp_mx2_human_review_decision_audit.json` | 已审计 |
| 2.2 观察/行动/反馈 | 验证标签不可预见；查询后反馈并更新 | `artifacts/mx2_validation_agent_observations.csv`；`src/materials_mvp/environment.py` | 已实现 |
| 2.3 记录与预算 | 8次查询、16条未揭示、逐轮可回放 | `artifacts/mx2_cross_formula_query_log.csv`；Run 43配置 | 已完成 |
| 3.1 发现信号 | D0—D4分层；负结果和异常提前定义 | `docs/discovery-signal-spec-3.1.md`；`src/materials_mvp/signal.py` | 已实现 |
| 3.2 参照 | Random、Static Top-N和同预算主策略 | `artifacts/mx2_cross_formula_seed_policy_results.csv` | 已完成 |
| 3.3 成败标准 | 双基线门槛、Bootstrap区间、防事后挑选 | Run 43预注册与结果；`artifacts/mx2_cross_formula_validation_summary.json` | 负向D3 |
| 4.1 一次试跑 | MP采集—审核—签署—隔离—查询闭环 | Run 40—43文档；逐轮日志 | 已完成 |
| 4.2 风险 | 方法不一致、二维性争议、泄漏和小样本 | `mp-1120746`隔离；标签承诺护照；失败审计 | 已留证 |
| 4.3 复现开源 | 配置、索引、日志、测试和密钥隔离 | `README.md`；`requirements*.txt`；`scripts/audit_public_release.py` | 已准备 |

## 结果说明

预注册主策略`Iterative w=0.35`在24条独立MX2验证候选上优于Random，但未超过Static Top-N，因此正向策略假设失败，并触发限定于该队列的D3负向发现。诊断策略`w=0.15`表现最好，但不能在观察结果后替换主策略。该结果的意义是：当前简单不确定性权重会付出探索机会成本，下一轮应在新的独立队列中预注册较低权重，同时保留Static Top-N作为必须超过的强参照。

## 不进入公开仓库的内容

账号、API密钥、原始API响应、验证oracle标签和本地虚拟环境只保存在Git忽略路径。160条随机记录位于独立测试夹具目录，仅用于软件闭环，不构成任何材料科学证据。
