# 第4次运行证据：网页注册与API用途确认

## 实际验证

- GitHub账号登录成功；
- Cloudflare人工验证完成；
- Materials Project注册条款由用户本人确认；
- 刷新后注册弹窗消失；
- Pourbaix应用正常显示搜索框、Generate操作和高级选项；
- API说明页可正常读取；
- 网站显示数据库版本为`v2026.04.13`，数据许可为CC BY 4.0。

## 与自动化调用有关的结论

Materials Project API页面明确将API用途描述为结构化访问当前数据库、分析、自动化工具开发、机器学习和大规模下载，并推荐使用官方`mp-api` Python客户端。因此：

- Cloudflare限制的是网页自动访问，不意味着禁止官方API程序调用；
- 网页适合登录、人工核查和使用交互式工具；
- 项目的可复现数据管线应使用API，而不是模拟网页点击批量抓取；
- API密钥只通过本地环境变量注入，不进入仓库、报告或日志。

## Pourbaix与本项目的关系

Pourbaix工具用于基于固体DFT数据和离子实验数据生成水溶液稳定性图。它不是当前Band Gap训练数据入口，也不替代Formation Energy或Energy Above Hull约束。除非后续把水相电化学稳定性纳入研究问题，否则该工具仅作为账户和网站可用性验证。

## PDF映射

- §2.1：固定真实数据源、数据库版本记录和API访问边界；
- §2.3：记录数据获取日期、版本、字段和查询预算；
- §4.2：网页人机验证、注册状态和网络环境是基础设施风险；
- §4.3：公开`mp-api`获取脚本和环境变量模板，按CC BY 4.0署名，不公开密钥。

## 下一验证点

在允许本地程序访问`api.materialsproject.org`的网络环境中运行`python scripts/probe_materials_project.py`，验证Summary字段；随后关联Robocrystallographer描述并设计二维性复核规则。

