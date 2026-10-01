# 复现主张

先创建论文，再用 `new claim` 创建 `<citekey>--<claim-slug>/`。一个目录对应一个可检验主张。真实代码和模拟放 online/，线下协议放 lab/，结果放 results/。资源未知时保留 route: null。

公共模板只提供通用 claim、可行性分析、计划与结果目录。专业实现放自己的 private 仓库，project.yaml.reproduction 使用 profile/private_extension/extension_data 声明接口；工具不会自动加载或执行扩展。

私有扩展读取 claim.yaml、research-profile.yaml 和关联论文的 03_reading/reading.md、04_analysis/analysis.yaml；写入本 claim 的 feasibility.md、plan.md、online/、lab/、results/。不覆盖原文，不把专业方向、真实资料或私有代码混入公共模板。
