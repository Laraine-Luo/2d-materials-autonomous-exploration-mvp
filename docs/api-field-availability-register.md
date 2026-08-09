# Materials Project API字段可获得性登记

## 登记状态说明

- **可直接请求**：Materials Project Summary API已知/请求字段，可由一次公式查询返回；最终以本地API响应审计为准。
- **不能直接获得**：不是该Summary响应中的原始字段，需要本项目派生、网页/结构审核、其他端点或实验外部证据。
- **待实测确认**：接口允许请求，但本机API连接成功前不宣称已返回。

## 字段登记

| 目标信息 | MP原字段/路径 | 当前判定 | 处理方式 |
|---|---|---|---|
| 候选ID | `material_id` | 可直接请求，待本次响应确认 | 作为候选主键 |
| 化学式 | `formula_pretty` | 可直接请求，待本次响应确认 | 映射为`formula` |
| 化学体系 | `chemsys` | 可直接请求，待本次响应确认 | 映射为`chemical_system` |
| 结构 | `structure` | 可直接请求，待本次响应确认 | 本地保存并生成结构特征 |
| Band Gap | `band_gap` | 可直接请求，待本次响应确认 | 映射为`band_gap_ev` |
| Formation Energy | `formation_energy_per_atom` | 可直接请求，待本次响应确认 | 主要稳定性指标 |
| Energy Above Hull | `energy_above_hull` | 可直接请求，待本次响应确认 | 辅助稳定性指标 |
| MP稳定标志 | `is_stable` | 可直接请求，待本次响应确认 | 辅助稳定性指标 |
| 更新时间 | `last_updated` | 可直接请求，待本次响应确认 | 数据漂移审计 |
| 数据库版本 | 网站版本页/响应环境，不是材料属性 | 不能作为单条Summary材料字段依赖 | 每次运行在审计元数据冻结记录 |
| 属性来源任务 | Summary `origins` | 官方文档确认可直接请求，待本次响应确认 | 找到属性对应`task_id` |
| 具体计算方法 | `origins.task_id`联查Thermo `entries[].parameters.run_type` | 不能由Summary一次查询直接获得 | 两步联查；缺失则进入方法审核队列，不得猜测 |
| 二维性结论 | `2D or Layered`网页证据+结构审核 | 不能由公式查询直接确定 | 派生`dimensionality_status`并人工审核 |
| 探索状态 | 环境运行产生 | 不能由MP获得 | 使用`exploration_status_*`字段 |
| D0—D4信号 | `signal.py`产生 | 不能由MP获得 | 按预注册规则判定 |
| 实验Band Gap/可合成性 | 外部实验/文献 | 不能由本主数据源直接获得 | 只进入D4外部验证，不混入主训练集 |

`scripts/probe_materials_project.py`每次执行都会覆盖生成`artifacts/materials_project_api_response_audit.json`，明确记录attempted/success/failed、时间、查询、返回数量、返回字段或失败类型。原始成功响应只保存在git忽略的`.local-data/`，API密钥永不写入审计文件。

本次实际执行结果为`failed`：运行环境在域名解析阶段返回`URLError [Errno 8]`，所以当前没有任何字段可登记为“本机API已返回”。该结果只说明当前传输环境失败，不等同于密钥无效。官方文档确认Summary支持按`formula`查询及通过`fields`选择`material_id`、`structure`、`band_gap`、`formula_pretty`等字段；计算泛函需要使用Summary的`origins`定位任务，再联查Thermo文档中的`run_type`。
