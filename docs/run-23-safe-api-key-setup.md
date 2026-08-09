# 第 23 次运行：API 类型确认与本地安全配置入口

## 1. 本次完成了什么

- 明确本项目只需要 Materials Project 主 API 的 `Your API Key`。
- 明确 MPContribs API 和 OPTIMADE API 不属于当前正式数据路径。
- 增加 macOS 本地运行入口 `scripts/setup_and_run_mp.command`。
- 入口采用隐藏输入，将密钥仅写入 `.local-secrets/materials_project.env`，权限设为仅当前用户可读写，然后运行正式管线。
- 脚本不会打印密钥，也不会把密钥写入日志、审计文件或公开仓库。

## 2. 对原有设计的落实与调整

- 保持 Materials Project 核心数据库为唯一正式科研数据源。
- MPContribs 是第三方贡献数据，当前不接入，避免来源和方法口径扩张。
- OPTIMADE 当前只提供标准化结构访问，不替代本项目所需的 Band Gap、Formation Energy、Energy Above Hull 等完整性质路径。
- 因旧密钥已经出现在聊天记录中，新增“轮换后再公开”的发布闸门。
- 新增安全输入脚本的理由：避免用户再次把新密钥粘贴进聊天、README、命令历史或 GitHub。

## 3. 对应初赛文稿哪些部分

- §2.1：固定唯一正式数据源和 API 类型。
- §2.2：主 API 返回结构与性质数据，构成正式反馈入口。
- §2.3：凭据不进入状态和探索日志，只记录请求是否成功。
- §4.2：降低密钥泄露、数据源混用和接口误用风险。
- §4.3：给出可复现但不泄露凭据的本地配置与运行方式。

## 4. 接下来讨论、设计与落地什么

1. 用户在 Materials Project Dashboard 生成新密钥并退休已经暴露的旧密钥。
2. 用户在 Finder 中双击或在终端运行 `scripts/setup_and_run_mp.command`，隐藏输入新密钥。
3. 若本机网络可用但缺少客户端，安装 `requirements-mp-api.txt` 后重跑。
4. API 成功后进入字段映射、12 条 MoS2 索引核对和人工审计。

