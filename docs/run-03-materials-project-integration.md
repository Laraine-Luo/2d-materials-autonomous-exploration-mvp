# 第3次运行证据：Materials Project接入试验

## 输入与目标

- 数据源选择：Materials Project；
- 探测对象：`mp-149`，仅用于验证Summary字段和连接，不声称其为二维材料；
- 请求字段：material ID、formula、Band Gap、formation energy per atom、energy above hull、stable flag；
- 凭证：从本地忽略目录读取，不写入请求日志和输出文档；
- 输出：只允许写入被Git忽略的`.local-data/`目录。

## 实际结果

脚本成功完成本地凭证读取和请求构造，但当前Codex执行环境在DNS解析阶段阻断外部网络，请求未到达Materials Project服务器。因此：

- 不能据此判断API密钥有效或无效；
- 不能据此判断字段请求是否被服务器接受；
- 可以确认仓库已具有不打印密钥的本地探测入口和隔离输出路径；
- 下一次需要在允许访问`api.materialsproject.org`的环境中原样重跑。

## 对问题定义的影响

Materials Project官方文档说明，Summary API适合材料筛选并可查询Band Gap等性质，但二维性不是Summary中的正式属性。官方示例建议将材料记录与Robocrystallographer描述关联以识别结构维度。因此真实数据管线至少包含两个阶段：

1. 获取电子性质与稳定性字段；
2. 使用Robocrystallographer描述并结合结构检查确认二维性。

这与冻结的第一部分一致：项目面向二维材料电子性质发现，但不能把数据库中的全部无机晶体直接当成二维候选空间。

## 官方依据

- Materials Project API Getting Started: https://docs.materialsproject.org/downloading-data/using-the-api/getting-started
- Querying Data: https://docs.materialsproject.org/downloading-data/using-the-api/querying-data
- API Examples, including dimensionality identification: https://docs.materialsproject.org/downloading-data/using-the-api/examples
