# 2D Materials Autonomous Exploration MVP  
# 二维材料自主探索最小可运行环境

A reproducible, finite-budget exploration environment for identifying audited 2D-material candidates whose Materials Project Band Gap lies in a target interval and whose stability fields satisfy fixed constraints.  
一个可复现的有限预算探索环境，用于识别Materials Project中Band Gap落入目标区间、且稳定性字段满足固定约束的已审核二维材料候选。

The repository supports the open-exploration competition project **“AI Autonomous Exploration Environment for Electronic-Property Discovery in 2D Materials — A Materials-Discovery Framework Based on Band Gap Prediction and Iterative Search.”**  
本仓库对应开放探索赛题项目：**“面向二维材料电子性质发现的AI自主探索环境——基于Band Gap预测与迭代搜索的材料发现框架”。**

> The 160 records under `data/test_fixture/` are randomly generated software-test data with no empirical or literature basis. They are never used as scientific evidence or substituted for Materials Project records.  
> `data/test_fixture/`中的160条记录是无经验或文献依据的随机软件测试数据，绝不作为科学证据，也不替代Materials Project正式记录。

## Submission result at a glance  
## 初赛结果概览

The formal scientific path uses **Materials Project only**, database version `2026.04.13`. Seven audited stable MoS2 records provide development labels; 24 human-approved MX2 records across MoSe2, MoTe2, WS2 and WSe2 form a label-isolated validation pool.  
正式科学路径只使用**Materials Project**，数据库版本为`2026.04.13`。7条已审核稳定MoS2记录提供开发标签；24条经人工批准、覆盖MoSe2、MoTe2、WS2和WSe2的MX2记录构成标签隔离验证池。

`mp-1120746` remains quarantined because its calculation-method cohort differs. No validation record is permitted in initial training.  
`mp-1120746`因计算方法队列不同继续隔离；任何验证记录都不得进入初始训练。

Each policy receives eight sequential queries over 20 shared seeds.  
每种策略在20个共同种子下获得8次顺序查询预算。

| Policy / 策略 | Role / 角色 | Mean D2 / 8 | Hit rate / 命中率 | Query MAE / eV |
|---|---|---:|---:|---:|
| Random | required baseline / 必需基线 | 2.60 | 32.50% | 0.3028 |
| Static Top-N | required baseline / 必需基线 | 3.85 | 48.13% | 0.2568 |
| Iterative `w=0.35` | preregistered primary / 预注册主策略 | 3.40 | 42.50% | 0.3021 |
| Iterative `w=0.15` | diagnostic only / 仅诊断 | 4.70 | 58.75% | 0.2234 |
| Pure uncertainty | diagnostic only / 仅诊断 | 1.85 | 23.13% | 0.4032 |

The primary policy exceeded Random by `+0.80 D2` (paired-bootstrap 95% CI `[0.10, 1.60]`) but trailed Static Top-N by `−0.45 D2` (95% CI `[−0.90, 0.00]`). It therefore failed the preregistered requirement to exceed both baselines.  
主策略相对Random提高`0.80 D2`（配对Bootstrap 95%区间`[0.10,1.60]`），但相对Static Top-N低`0.45 D2`（区间`[-0.90,0.00]`），因此没有达到同时超过两条基线的预注册要求。

This is reported as a **D3 negative strategy signal scoped to the fixed MX2 validation cohort**, not as universal evidence against active learning.  
该结果登记为**限定于固定MX2验证队列的D3负向策略信号**，不外推为主动学习普遍无效。

The diagnostic `w=0.15` performed best descriptively, but the anti-cherry-pick rule forbids replacing the primary policy after seeing the result. It is a hypothesis for the next independent cohort.  
诊断策略`w=0.15`的描述性表现最好，但防事后挑选规则禁止在看到结果后替换主策略；它只能作为下一独立队列的待检验假设。

Evidence: [`docs/run-43-cross-formula-validation-result.md`](docs/run-43-cross-formula-validation-result.md), [`config/mx2_cross_formula_validation_v1.json`](config/mx2_cross_formula_validation_v1.json), and [`docs/submission-evidence-index.md`](docs/submission-evidence-index.md).  
证据见：[`docs/run-43-cross-formula-validation-result.md`](docs/run-43-cross-formula-validation-result.md)、[`config/mx2_cross_formula_validation_v1.json`](config/mx2_cross_formula_validation_v1.json)和[`docs/submission-evidence-index.md`](docs/submission-evidence-index.md)。

## What the environment proves  
## 环境证明了什么

1. A validation Band Gap label is hidden until a policy spends one query.  
   验证集Band Gap标签在策略消耗一次查询前保持隐藏。
2. Candidates that fail the Formation Energy-centred stability rule are excluded before selection.  
   未通过以Formation Energy为主的稳定性规则的候选，在策略选择前即被排除。
3. All policies share the same initial knowledge, validation pool, target interval, stability rule, seeds and budget.  
   所有策略共享相同的初始知识、验证池、目标区间、稳定性规则、种子和预算。
4. Iterative policies predict, select, receive feedback, update the model and continue.  
   迭代策略执行预测、选择、获得反馈、更新模型并继续探索。
5. Random and frozen-model Static Top-N run through the same environment as required baselines.  
   Random和冻结模型的Static Top-N作为必需基线，在同一环境中运行。
6. Every observation, decision, reason, feedback value, signal and budget position is logged.  
   每次观察、决策、理由、反馈值、信号和预算位置均写入日志。

## Fixed scientific rules  
## 固定科学规则

The target Band Gap interval is `1.5–2.5 eV`.  
目标Band Gap区间为`1.5–2.5 eV`。

Formation Energy is the primary stability condition, with auxiliary support from Energy Above Hull or the Materials Project `is_stable` flag:  
Formation Energy是主要稳定性条件，Energy Above Hull或Materials Project的`is_stable`标记提供辅助支持：

\[
S(x)=\mathbf 1[E_f(x)\le-0.2]\land
\mathbf 1[E_{hull}(x)\le0.1\lor is\_stable(x)].
\]

These thresholds are preregistered MVP evaluation rules, not universal synthesizability criteria. Real MP properties are classified, never generated or corrected by the synthetic fixture equations.  
这些阈值是预注册的MVP评价规则，不是普遍可合成判据。正式MP性质只被分类，不会被测试夹具中的合成公式生成或校正。

Only `confirmed_2d` records from the frozen method and database-version cohort may enter a scientific pool. `uncertain_2d` records remain visible in audit statistics but cannot enter training without human approval.  
只有来自冻结方法队列和数据库版本、状态为`confirmed_2d`的记录才能进入科学候选池；`uncertain_2d`记录保留在审计统计中，但未经人工批准不得进入训练。

## Predictor and policies  
## 预测器与探索策略

The Band Gap predictor is ridge regression with `λ=0.1`:  
Band Gap预测器采用`λ=0.1`的岭回归：

\[
\hat\beta=\arg\min_\beta\left(\lVert y-X\beta\rVert_2^2+\lambda\lVert\beta\rVert_2^2\right).
\]

Twelve bootstrap ridge models provide predictive mean `ȳ(x)` and an uncalibrated uncertainty proxy `u(x)`, defined as prediction standard deviation.  
12个Bootstrap岭模型提供预测均值`ȳ(x)`以及以预测标准差定义的未校准不确定性代理`u(x)`。

- Random samples uniformly from the eligible pool.  
  Random从合格候选池均匀抽样。
- Static Top-N freezes the initial model and ranks candidates by target-interval score.  
  Static Top-N冻结初始模型，并按目标区间得分排序。
- The primary Iterative policy retrains after each revealed label and maximizes:  
  主Iterative策略在每次标签揭示后重训，并最大化：

\[
A(x)=0.65T(\bar y(x))+0.35\frac{u(x)}{\max_{x'}u(x')}.
\]

These are deliberately simple and auditable MVP methods. They are not presented as Expected Improvement, UCB, calibrated uncertainty or a physical law.  
这些是有意保持简单、可审计的MVP方法，不被包装为Expected Improvement、UCB、校准不确定性或物理定律。

Full formulas and the unsupported synthetic test-data equations are documented in [`docs/methodology-and-report-mapping.md`](docs/methodology-and-report-mapping.md).  
完整公式以及无科学依据的合成测试数据生成式见[`docs/methodology-and-report-mapping.md`](docs/methodology-and-report-mapping.md)。

## What counts as discovery  
## 什么算发现

| Level / 等级 | Evidence meaning / 证据含义 | Current boundary / 当前判定边界 |
|---|---|---|
| D0 | traceable technical or index event / 可追踪技术或索引事件 | implemented; proves traceability only / 已实现，只证明可追踪 |
| D1 | real MP Band Gap in target interval / 真实MP Band Gap数值命中 | implemented; called a numerical hit only / 已实现，只称数值命中 |
| D2 | D1 plus identity, 2D, stability, method and quality audit / D1加身份、二维性、稳定性、方法和质量审核 | implemented; audited candidate signal / 已实现，可称已审核候选信号 |
| D3 | reproducible pattern or negative result in holdout/repeated evaluation / 留出或重复评价中稳定复现的规律或负结果 | this run claims only the scoped MX2 negative strategy signal / 本轮只主张限定范围的MX2负向策略信号 |
| D4 | high-accuracy calculation, independent data, literature or experiment / 高精度计算、独立数据、文献或实验验证 | not reached; no new-material claim / 未达到，不声明发现新材料 |

A single query can be classified automatically only up to D2. D3 requires preregistered repeated or independent validation; D4 requires external validation.  
单次查询最高只能自动判定到D2；D3需要预注册的重复或独立验证，D4需要外部验证。

An anomaly is flagged when `|predicted Band Gap − MP Band Gap| > max(0.6 eV, 2u)`. It enters human review and cannot contaminate training before approval.  
当`|预测Band Gap−MP Band Gap| > max(0.6 eV, 2u)`时标记异常；异常进入人工审核，批准前不得回流训练造成污染。

Executable scope: [`src/materials_mvp/signal.py`](src/materials_mvp/signal.py). Full specification: [`docs/discovery-signal-spec-3.1.md`](docs/discovery-signal-spec-3.1.md).  
可执行范围见[`src/materials_mvp/signal.py`](src/materials_mvp/signal.py)，完整规范见[`docs/discovery-signal-spec-3.1.md`](docs/discovery-signal-spec-3.1.md)。

## Materials Project identity and mapping  
## Materials Project身份与映射

The scientific design has one primary source: **Materials Project only**. MPContribs, OPTIMADE, web-transcribed values and synthetic records do not enter the formal scientific pool.  
科学设计只有一个主要数据源：**Materials Project**。MPContribs、OPTIMADE、网页人工抄录值和合成记录均不进入正式科学候选池。

For MoS2, the recorded index path is `Materials Explorer → Mo–S → MoS2 → MP ID`. `MoS2` is the formula/composition layer, while each MP ID identifies an individual structure candidate.  
MoS2的索引路径记录为`Materials Explorer → Mo–S → MoS2 → MP ID`。其中MoS2是化学式／组成层，单个MP ID才对应一条独立结构候选。

Original MP field names and canonical mapped names are listed one-to-one in [`config/materials_project_mapping_list.json`](config/materials_project_mapping_list.json). Derived exploration-state fields use the `exploration_status_` prefix.  
MP原字段名与规范映射名在[`config/materials_project_mapping_list.json`](config/materials_project_mapping_list.json)中一一对应登记；派生探索状态字段统一使用`exploration_status_`前缀。

The official `mp-api` client is pinned in `requirements-mp-api.txt`. Raw successful responses and oracle labels remain in ignored `.local-data/`; credentials remain in ignored `.local-secrets/`.  
官方`mp-api`客户端版本固定在`requirements-mp-api.txt`中。成功的原始响应和oracle标签保存在Git忽略的`.local-data/`，凭据保存在Git忽略的`.local-secrets/`。

Because a development key was disclosed outside the repository, rotate it on the Materials Project Dashboard before publishing GitHub. Never place the replacement in chat, README or source files.  
由于开发阶段的密钥曾在仓库之外披露，公开GitHub前必须在Materials Project Dashboard轮换；新密钥不得写入对话、README或源文件。

## Reproduce the minimum environment  
## 复现最小环境

The dependency-free synthetic interface check requires Python 3.10+:  
无第三方依赖的合成接口检查需要Python 3.10或更高版本：

```bash
python scripts/run_demo.py
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/audit_public_release.py --root .
```

The commands generate comparable policy summaries, per-query logs, dimensionality audits and a public-release audit.  
这些命令会生成可比较的策略汇总、逐查询日志、二维性审计和公开发布审计。

Formal MP acquisition requires Python 3.11+, the pinned official client and a locally stored API key:  
正式MP采集需要Python 3.11或更高版本、固定版本的官方客户端和本地保存的API密钥：

```bash
python -m pip install -r requirements-mp-api.txt
python scripts/run_formal_mp_pipeline.py
```

The pipeline fails closed: acquisition, identity, version, method or review failure stops promotion and never substitutes synthetic or web-transcribed data.  
流水线采用失败关闭：采集、身份、版本、方法或审核任一失败都会停止晋级，绝不以合成或网页抄录数据替代。

## Repository evidence map  
## 仓库证据索引

| Path / 路径 | Purpose / 用途 |
|---|---|
| `config/mx2_cross_formula_validation_v1.json` | frozen Run 43 protocol / Run 43冻结协议 |
| `artifacts/mx2_cross_formula_validation_summary.json` | aggregate result and confidence intervals / 汇总结果与置信区间 |
| `artifacts/mx2_cross_formula_query_log.csv` | replayable per-query evidence / 可回放逐查询证据 |
| `artifacts/mx2_validation_agent_observations.csv` | label-free Agent observation interface / 无标签Agent观察接口 |
| `artifacts/mx2_validation_passports/` | public label commitments and audit state / 公开标签承诺与审核状态 |
| `docs/submission-evidence-index.md` | PDF §1.1–4.3 crosswalk / PDF第1.1—4.3节证据映射 |
| `docs/mp-mx2-validation-index-catalog.md` | repository-visible MP index catalogue / 仓库可见MP索引清单 |
| `scripts/build_four_page_pdf.py` | reproducible four-page PDF builder / 可复现四页PDF生成器 |

Historical runs and failed paths remain under `docs/run-*` and `artifacts/invalid_*`; they are retained for audit and are not silently merged into the final claim.  
历史运行和失败路径保留在`docs/run-*`及`artifacts/invalid_*`中，用于审计，不会被静默合并进最终结论。

## Current limits  
## 当前边界

- The environment searches a fixed candidate pool and does not generate structures or run DFT.  
  环境只搜索固定候选池，不生成结构，也不运行DFT。
- Formation Energy is known metadata and a hard pre-filter in the current MVP.  
  当前MVP把Formation Energy作为已知元数据和硬筛选条件。
- Bootstrap spread is an uncalibrated uncertainty proxy.  
  Bootstrap离散度是未校准的不确定性代理。
- MP Band Gaps are computational proxy values, not experimental truth.  
  MP Band Gap是计算代理值，不是实验真值。
- The D3 result is scoped to one fixed MX2 validation cohort.  
  D3结果只适用于当前固定MX2验证队列。
- No LLM, DeepSeek, LangGraph or MCP is used.  
  本项目未使用LLM、DeepSeek、LangGraph或MCP。

These boundaries are part of the submission result, not omissions to be hidden.  
这些边界是提交结论的一部分，不是需要隐藏的缺陷。

