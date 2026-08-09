# GitHub 公开发布准备清单

本页用于初赛 PDF §4.3“复现与开源计划”的实现证据。它不改变已冻结的 PDF 第一大点，也不把测试数据或网页抄录记录升级为科研证据。

## 已具备

- 一条命令运行 160 条随机测试数据上的最小闭环：`python scripts/run_demo.py`。
- 一条命令运行 13 项单元测试：`PYTHONPATH=src python -m unittest discover -s tests -v`。
- GitHub Actions 自动执行测试、闭环演示和公开内容审计。
- `data/test_fixture/` 与 Materials Project 正式数据路径严格分离。
- `.local-secrets/`、`.local-data/`、`.venv/` 和 `outputs/` 不进入公开仓库。
- API 失败、映射阻断、候选晋级阻断均保留机器可读审计记录。
- MoS2 的 12 条网页索引清单、审核队列、证据护照和准备度页面均可在仓库检查。

## 发布前必须人工完成

1. 轮换曾在聊天或界面中暴露过的 Materials Project API 密钥，并仅在本地环境变量中使用新密钥。
2. 确认公开仓库名称、所有者和许可证署名；不要虚构团队信息。
3. 在可联网终端完成一次官方 `mp-api` 拉取，并检查 API 审计为成功状态。
4. 完成 MoS2 记录的人工二维性与计算方法一致性审核；不足 8 条合格记录时不得运行正式闭环。
5. 运行 `python scripts/audit_public_release.py --root .`，要求结果为 `pass`。
6. 创建公开仓库后，再生成真实仓库短链接/二维码并写入最终 PDF；当前不得使用占位二维码。

## 建议公开仓库名称

`2d-materials-autonomous-exploration-env`

名称突出“可复现探索环境”，避免把当前 D0—D2 证据包装成已经完成的材料发现。

## PDF §4.3 可采用的证据表述

> 项目计划以公开 GitHub 仓库发布。仓库提供固定配置、一键闭环演示、单元测试、GitHub Actions 自动复现检查、逐轮探索日志及 Materials Project 数据审计链。本地凭据与原始 API 响应通过目录隔离和公开发布审计排除。正式数据演练仅接受通过 API 来源、数据库版本、二维性、计算方法及必需字段审核的记录。

该表述只能在自动检查通过后使用；它说明的是复现机制和开源边界，不等同于真实材料发现结果。
