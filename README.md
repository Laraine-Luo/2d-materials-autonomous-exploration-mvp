# 2D Materials Autonomous Exploration Environment  
# 二维材料电子性质 AI 自主探索环境

**A materials-discovery framework based on Band Gap prediction and iterative search.**  
**基于 Band Gap 预测与迭代搜索的材料发现框架。**

A reproducible, finite-budget environment for exploring audited 2D-material candidates whose Materials Project Band Gap lies in a target interval and whose stability metadata satisfies predefined constraints.  
一个可复现的有限预算探索环境，用于搜索 Materials Project 中 Band Gap 位于目标区间且满足稳定性约束的已审核二维材料候选。

The project implements a **prediction → selection → feedback → update → continued exploration** loop rather than a one-time property-prediction task.  
项目实现“**预测—选择—反馈—更新—继续探索**”闭环，而不是一次性的性质预测任务。

> **Data warning / 数据声明**  
> The 160 records under `data/test_fixture/` are randomly generated software-test data without empirical, Materials Project or literature basis. They are used only to verify the software loop and never as scientific evidence.  
> `data/test_fixture/` 中的160条记录是无实验、Materials Project或文献依据的随机软件测试数据，只用于验证程序闭环，绝不作为科学证据。


## 1. Research problem / 研究问题

Materials Project and C2DB have accumulated extensive structural and calculated-property data, but efficiently searching a large candidate space for materials satisfying both target electronic properties and stability constraints remains challenging.  
Materials Project、C2DB等数据库已积累大量结构与计算性质数据，但如何高效搜索同时满足目标电子性质与稳定性约束的材料仍具有挑战性。

Machine learning and active learning are already used in materials science. This project does not claim otherwise. It focuses on structuring a task-specific environment with unified observation, action, feedback, budget, audit, discovery signals and baseline evaluation.  
机器学习与主动学习已经应用于材料研究。本项目并不否认已有工作，而是聚焦于建立具有统一观察、行动、反馈、预算、审核、发现信号和基线评价的特定任务环境。

**Research slice / 研究切片：**

> Under a fixed Materials Project candidate pool and finite query budget, can a sequential Agent efficiently identify audited 2D candidates whose Band Gap is `1.5–2.5 eV` and whose stability metadata passes a preregistered rule?  
> 在固定Materials Project候选池和有限查询预算下，序贯决策Agent能否高效识别Band Gap位于`1.5–2.5 eV`且通过预注册稳定性规则的已审核二维材料候选？

The environment does not generate structures, run online DFT or claim experimental synthesizability.  
本环境不生成新结构、不在线运行DFT，也不声明实验可合成性。

---

## 2. Formal validation / 正式验证

The formal scientific path uses **Materials Project only**, database version `2026.04.13`.  
正式科学路径仅使用**Materials Project**，数据库版本为`2026.04.13`。

- 7 audited stable MoS2 records form the development knowledge set.  
  7条已审核稳定MoS2记录构成开发知识集。
- 24 human-approved MX2 records across MoSe2, MoTe2, WS2 and WSe2 form the holdout validation pool.  
  24条经人工批准的MoSe2、MoTe2、WS2和WSe2记录构成留出验证池。
- `mp-1120746` remains quarantined because its calculation-method cohort differs.  
  `mp-1120746`因计算方法队列不一致继续隔离。
- No validation record enters initial training.  
  任何验证记录均不得进入初始训练。
- Each policy receives 8 sequential queries over 20 shared seeds.  
  每种策略在20个共同种子下获得8次顺序查询预算。

The 20 seeds are repeated algorithmic trajectories over the same validation pool, not 20 independent material datasets.  
20个种子表示同一验证池上的20条算法运行轨迹，不是20份独立材料数据集。

| Policy / 策略 | Role / 角色 | Mean D2/8* | Hit rate / 命中率 | MAE/eV |
|---|---|---:|---:|---:|
| Random | baseline / 基线 | 2.60 | 32.50% | 0.3028 |
| Static Top-N | baseline / 基线 | 3.85 | 48.13% | 0.2568 |
| Iterative `w=.35` | primary / 主策略 | 3.40 | 42.50% | 0.3021 |
| Iterative `w=.15` | diagnostic / 诊断 | 4.70 | 58.75% | 0.2234 |
| Pure uncertainty | diagnostic / 诊断 | 1.85 | 23.13% | 0.4032 |

> *: {Mean D2/8}=\frac{1}{20}\sum_{s=1}^{20}N^{(s)}_{D2}\)

The primary policy exceeded Random by `+0.80 D2`, with paired-bootstrap 95% CI `[0.10,1.60]`, but trailed Static Top-N by `−0.45 D2`, with CI `[−0.90,0.00]`.  
主策略比Random平均多`0.80`个D2，配对Bootstrap 95%区间为`[0.10,1.60]`；但比Static Top-N少`0.45`个，区间为`[-0.90,0.00]`。

It therefore failed the preregistered requirement to exceed both baselines. This is reported as a **D3 negative strategy signal limited to the fixed MX2 cohort**, not as evidence that active learning is universally ineffective.  
因此，主策略未达到同时超过两条基线的预注册标准。该结果登记为**仅适用于固定MX2队列的D3负向策略信号**，不能外推为主动学习普遍无效。

Although diagnostic `w=.15` performed best descriptively, it cannot replace the primary policy after observing the results. It is retained as a hypothesis for the next independent cohort.  
虽然诊断策略`w=.15`描述性表现最好，但不能在观察结果后替换主策略，只能作为下一独立队列的待检验假设。

Evidence / 证据：

- [`docs/run-43-cross-formula-validation-result.md`](docs/run-43-cross-formula-validation-result.md)
- [`config/mx2_cross_formula_validation_v1.json`](config/mx2_cross_formula_validation_v1.json)
- [`artifacts/mx2_cross_formula_validation_summary.json`](artifacts/mx2_cross_formula_validation_summary.json)
- [`artifacts/mx2_cross_formula_query_log.csv`](artifacts/mx2_cross_formula_query_log.csv)

---

## 3. Environment interface / 环境接口

### Fixed rules / 固定规则

The Agent cannot change the MP version, candidate identities, target interval, stability thresholds, features, hidden labels, budget, seeds, strategies or audit decisions.  
Agent不能修改MP版本、候选身份、目标区间、稳定性阈值、特征、隐藏标签、预算、种子、策略或审核结论。

This is an **offline replay environment using historical MP calculations**, not an online DFT or experimental system.  
这是一个使用MP历史计算数据的**离线回放环境**，不是在线DFT或实验系统。

### Observation / 观察

The Agent observes MP ID, formula, five structural features, prediction, uncertainty, stability metadata, audit state, exploration history and remaining budget.  
Agent可观察MP ID、化学式、五项结构特征、预测值、不确定性、稳定性元数据、审核状态、历史记录和剩余预算。

The five features are `n_sites`, `volume_per_atom`, `density`, `lattice_anisotropy` and `layer_component_count`.  
五项特征为`n_sites`、`volume_per_atom`、`density`、`lattice_anisotropy`和`layer_component_count`。

Unqueried validation Band Gaps remain hidden.  
尚未查询的验证Band Gap保持隐藏。

### Action and feedback / 行动与反馈

The Agent selects the next eligible MP ID. One query consumes one budget unit and reveals its MP Band Gap, prediction error, target-hit state, D0–D2 signal and audit status.  
Agent选择下一条合格MP ID。每次查询消耗一个预算单位，并返回其MP Band Gap、预测误差、目标命中状态、D0—D2信号和审核状态。

Approved feedback labels are added to the known set only for Iterative policies, after which the model is retrained.  
只有Iterative策略会将经批准的反馈标签加入已知集并重新训练模型。

The Agent is an algorithmic sequential decision-maker, not a conversational LLM Agent.  
这里的Agent是算法序贯决策主体，不是聊天式大模型。

### Logging / 日志

Each query records round, policy, MP ID, prediction, uncertainty, revealed label, error, stability, dimensionality, selection reason, signal level, review state and budget position.  
每次查询记录轮次、策略、MP ID、预测、不确定性、揭示标签、误差、稳定性、二维性、选择理由、信号等级、审核状态和预算位置。

`uncertain_2d` records remain visible in audit statistics but cannot enter training before human approval.  
`uncertain_2d`记录保留在审计统计中，但未经人工批准不得进入训练。

---

## 4. Data and stability / 数据与稳定性

The formal scientific pool uses Materials Project only. MPContribs, OPTIMADE, web-transcribed values and synthetic records do not enter formal training or validation.  
正式科学候选池只使用Materials Project。MPContribs、OPTIMADE、网页抄录值和合成记录均不进入正式训练或验证。

MoS2 is indexed as:  
MoS2的索引层级为：

```text
Materials Explorer → Mo–S → MoS2 → MP ID
```

`MoS2` is a formula layer; each MP ID identifies an individual structural candidate.  
`MoS2`是化学式层，具体MP ID才标识一条独立结构候选。

Field mappings are recorded in [`config/materials_project_mapping_list.json`](config/materials_project_mapping_list.json). Derived state fields use the `exploration_status_` prefix.  
字段映射见[`config/materials_project_mapping_list.json`](config/materials_project_mapping_list.json)，派生状态字段统一使用`exploration_status_`前缀。

Formation Energy is the primary stability condition; Energy Above Hull and MP `is_stable` provide auxiliary evidence:

\[
S(x)=\mathbf1[E_f\le-0.2]\land\mathbf1[E_{hull}\le0.1\lor is\_stable].
\]

Formation Energy是主要稳定性条件；Energy Above Hull和MP的`is_stable`提供辅助证据。

These thresholds are preregistered MVP evaluation rules, not universal synthesizability criteria. Real MP values are never generated or corrected by synthetic fixture equations.  
这些阈值是预注册的最小环境评价规则，不是普遍可合成判据。真实MP值绝不会由合成测试公式生成或校正。

---

## 5. Predictor and policies / 预测器与策略

The predictor is ridge regression with `λ=0.1`:

\[
\hat\beta=\arg\min_\beta\left(\lVert y-X\beta\rVert_2^2+\lambda\lVert\beta\rVert_2^2\right).
\]

预测器采用`λ=0.1`的岭回归。

Twelve bootstrap ridge models provide predictive mean \(\bar y(x)\); their standard deviation is used as an uncalibrated uncertainty proxy \(u(x)\).  
12个Bootstrap岭模型提供预测均值\(\bar y(x)\)，模型预测标准差作为未校准的不确定性代理\(u(x)\)。

For target interval \([L,H]=[1.5,2.5]\) eV:

\[
T(\hat y)=
\begin{cases}
1,&L\le\hat y\le H,\\
\frac{1}{1+\min(|\hat y-L|,|\hat y-H|)},&\text{otherwise}.
\end{cases}
\]

| Policy / 策略 | Rule / 规则 |
|---|---|
| Random | \(x_{next}\sim Uniform(C_{eligible}\setminus C_{queried})\) |
| Static Top-N | \(x_{next}=\arg\max_xT(\bar y_0(x))\); frozen model / 模型冻结 |
| Iterative | \(A(x)=(1-w)T(\bar y(x))+w\,u(x)/\max u\); retrain after feedback / 反馈后重训 |

The primary Iterative policy uses `w=.35`; `w=.15` is diagnostic only.  
主Iterative策略使用`w=.35`；`w=.15`仅用于诊断。

These are deliberately simple, auditable MVP rules—not Expected Improvement, UCB, calibrated Bayesian optimization or physical laws.  
这些是有意保持简单、可审计的最小环境规则，不是Expected Improvement、UCB、校准贝叶斯优化或物理定律。

---

## 6. Discovery signals / 发现信号

| Level / 等级 | Meaning / 含义 |
|---|---|
| D0 | traceable API, index or audit event / 可追踪API、索引或审核事件 |
| D1 | real MP Band Gap hits target interval / 真实MP Band Gap命中目标区间 |
| D2 | D1 plus identity, 2D, stability, method and quality audit / D1加身份、二维性、稳定性、方法和质量审核 |
| D3 | reproducible pattern, negative result or failure mode / 可复现规律、负结果或失败模式 |
| D4 | external calculation, independent data, literature or experiment / 外部计算、独立数据、文献或实验验证 |

A single query can reach at most D2 automatically. D3 requires preregistered repeated or independent validation; D4 requires external evidence.  
单次查询最高只能自动达到D2；D3需要预注册重复或独立验证，D4需要外部证据。

An anomaly is flagged when:

\[
|\hat E_g-E_g^{MP}|>\max(0.6\text{ eV},2u).
\]

Anomalies enter human review and cannot contaminate training before approval.  
异常进入人工审核，批准前不得回流训练造成污染。

Executable rules: [`src/materials_mvp/signal.py`](src/materials_mvp/signal.py)  
可执行规则：[`src/materials_mvp/signal.py`](src/materials_mvp/signal.py)

Full specification: [`docs/discovery-signal-spec-3.1.md`](docs/discovery-signal-spec-3.1.md)  
完整规范：[`docs/discovery-signal-spec-3.1.md`](docs/discovery-signal-spec-3.1.md)

---

## 7. Reproduction / 复现

Software-only closed-loop check, requiring Python 3.10+:  
软件最小闭环检查，需要Python 3.10+：

```bash
python scripts/run_demo.py
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/audit_public_release.py --root .
```

Formal MP acquisition requires Python 3.11+ and the pinned official client:  
正式MP采集需要Python 3.11+和固定版本官方客户端：

```bash
python -m pip install -r requirements-mp-api.txt
./scripts/setup_and_run_mp.command
```

The API key is stored only under Git-ignored `.local-secrets/`. Never place credentials in source files, README, commits or public logs.  
API密钥仅保存在Git忽略的`.local-secrets/`中，禁止写入源文件、README、提交记录或公开日志。

The pipeline fails closed: acquisition, version, identity, method, dimensionality or review failure stops promotion and never substitutes synthetic data.  
流水线采用失败关闭：采集、版本、身份、方法、二维性或审核任一失败都会停止晋级，绝不以合成数据替代。

---

## 8. Repository map / 仓库索引

| Path / 路径 | Purpose / 用途 |
|---|---|
| `src/materials_mvp/` | environment, model and signal code / 环境、模型与信号代码 |
| `config/` | frozen protocols and mappings / 冻结协议与字段映射 |
| `artifacts/` | summaries and replayable logs / 汇总与可回放日志 |
| `docs/` | methods, audits and run reports / 方法、审核与运行报告 |
| `data/test_fixture/` | synthetic software tests only / 仅供软件测试的合成数据 |
| `scripts/` | execution and audit entry points / 运行与审计入口 |
| `tests/` | automated tests / 自动测试 |

Detailed report-to-repository mapping: [`docs/submission-evidence-index.md`](docs/submission-evidence-index.md)  
报告与仓库详细映射：[`docs/submission-evidence-index.md`](docs/submission-evidence-index.md)

---

## 9. Current limits / 当前边界

- Fixed candidate search; no structure generation. / 固定候选池搜索，不生成结构。
- Offline MP replay; no real-time DFT or experiment. / 离线MP回放，不实时运行DFT或实验。
- Formation Energy is a known hard pre-filter. / Formation Energy是已知硬筛选条件。
- Bootstrap spread is uncalibrated. / Bootstrap离散度未经校准。
- MP Band Gaps are computational proxies, not experimental truth. / MP Band Gap是计算代理值，不是实验真值。
- The D3 result is limited to the fixed MX2 cohort. / D3结果仅适用于固定MX2队列。
- Feature-importance and material-family patterns remain future hypotheses. / 特征重要性和材料族规律仍是未来假设。
- No LLM, DeepSeek, LangGraph or MCP is used. / 未使用LLM、DeepSeek、LangGraph或MCP。

These boundaries are part of the scientific result, not omissions to be hidden.  
这些边界属于科学结论的一部分，不是需要隐藏的缺陷。

---

## 10. Open source and references / 开源与参考资料

The initial-submission snapshot should be published as a fixed GitHub Release with its commit hash recorded. Later main-branch updates must not overwrite the submission snapshot.  
初赛快照应发布为固定GitHub Release并登记commit hash；后续主分支更新不得覆盖提交快照。

Materials Project source, version and CC BY 4.0 attribution must be disclosed. Credentials, raw local responses and hidden oracle labels must not be uploaded.  
应披露Materials Project来源、版本和CC BY 4.0署名；凭据、本地原始响应和隐藏oracle标签不得上传。

1. Horton, M. K. et al. *Nature Materials* **24**, 1522–1532 (2025).
2. Gjerding, M. N. et al. *2D Materials* **8**, 044002 (2021).
3. Lookman, T. et al. *npj Computational Materials* **5**, 21 (2019).
4. [Materials Project API documentation](https://docs.materialsproject.org/downloading-data/using-the-api)
5. [Materials Project electronic-structure methodology](https://docs.materialsproject.org/methodology/electronic-structure)

Repository code is released under [`LICENSE`](LICENSE). Materials Project data remain subject to its terms and CC BY 4.0 requirements.  
仓库代码按照[`LICENSE`](LICENSE)发布；Materials Project数据仍受其使用条款与CC BY 4.0要求约束。
