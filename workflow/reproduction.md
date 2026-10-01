# 复现功能地图

复现扩展通过 `INDEX.json` 和 ArtifactRef 解析 paper、analysis、formula、concept、principle、claim。稳定 ID 与任务合同见 [task-orchestration.md](task-orchestration.md)。`repro-feasibility` / `repro-plan` 使用同一 context → result → review → accept 闭环；私有实现提交草稿，主模型验收后应用正式产物。短公式 ID 和旧 claim_id 保留兼容，跨文件连接使用规范 ID。公共模板只定义连接和验收接口，专业实验执行等待后续配置。

## 核心输入与输出

每项分析读取论文/claim 及项目 research-profile.yaml。逐项匹配代码、数据、算力、软件、设备、耗材、实验室、技能、时间、预算、伦理与合规。未知资源不能算作具备；低置信度不能伪装为最终判定。

claim.yaml 保存唯一主张事实与状态，feasibility.md 保存资源证据、替代方案和风险，plan.md 保存步骤与依赖。三个目录 online、lab、results 承接线上代码/模拟、线下协议和真实结果。具体字段见 workflow/schemas.yaml 的 claim 契约与现有模板。

文献接口使用 03_reading/reading.md、04_analysis/analysis.yaml 的 extraction（证据抽取）、formulas（公式）、reproduction（候选和信号）；身份与状态仍从 meta.yaml 获取。旧平铺路径保留兼容，不继续作为新输出接口。

## 路线判断框架

| route | 适用情形 | 所需证据 |
|---|---|---|
| online-code | 可通过代码与可获取数据检验原 claim | 方法、数据、实现、算力、指标 |
| online-simulation | 可通过模拟检验明确限定的性质 | 模型假设、参数、适用范围、与原 claim 差异 |
| offline-lab | 依赖物理实验或现场采样 | 实验室权限、设备耗材、协议、伦理 |
| hybrid | 代码和线下实验都不可缺少 | 两端资源及数据交接 |
| observe-only | 当前只能阅读或分析已有结果 | 当前阻碍、可观察部分与限制 |
| unreproducible | 有证据证明在声明范围内无法实施 | 明确阻断依据，不可仅以资料缺失判定 |

当前占位判断是 `route: null, confidence: null`，表示尚未分析；CLI 不根据关键词自动分类，也不伪造可行性。三个角色可用 mock 走通空流程。

## 最小可行复现

先确定待检验的最小主张、数据与基线、评价指标、随机性、允许误差和停止条件，再明确环境依赖、数据准备、smoke test、baseline 和目标实验里程碑。不能统一用某个相对误差阈值替代论文具体指标与波动范围。

线上目录按需添加环境、代码、数据准备、baseline、指标和运行说明；线下目录按需添加协议、设备耗材、安全伦理、记录规范和数据交接。没有实验室条件时仍可提出待确认线下方案，但不能声称可执行。模拟方案应明确它能检验哪些结论，不能替代物理证据。

## 扩展点

project.yaml.reproduction 固定包含 profile（默认 generic）、private_extension（默认 TODO(user)）、extension_data（对象）。这些只是接口声明，不自动加载脚本或执行实验；公共模板不硬编码专业方向。

专业实现建立独立 private 仓库。扩展读取 claim.yaml、research-profile.yaml、关联论文 03_reading/reading.md 和 04_analysis/analysis.yaml；写入对应 claim 的 feasibility.md、plan.md、online/、lab/、results/。私有内容不回传公共模板。

REP-001：后续实现论文到代码映射、环境验证、数据版本、种子与运行记录、指标比较、模拟与实验协议。真实实验均需先 dry-run 或明确授权。本轮只有模板、schema、prompt、空分类和 mock；没有训练、模拟、实验室控制或科学验证结果。
