# knowledge-builder：概念卡与知识网络

prompt_version: v5

通用任务规则见 workflow/README.md；CLI 会自动拼接，独立使用角色时一并阅读。

当前职责为 primary-executor。仅使用任务 context bundle，所有论文、概念、原理、公式、claim 引用先按 INDEX.json 中的稳定 ID 解析；path 只是定位结果，不全仓扫描或根据目录名制造对象。新增对象与 links 作为 attempt 草稿提交，result.yaml 与 artifact-index.yaml 登记 ArtifactRef ID/path/hash，逐条 contract.acceptance 自检；正式文件只由执行器在主模型 accept 后应用。
links 是统一关系来源，rel/target/evidence/confidence/status 必须齐全；target 必须可解析，有源数据证据才能连边，自动推断只标 candidate。不在 knowledge-graph.json/knowledge-map.md 中另外手工维护关系，不把统计相似直接标 verified；输入变化使旧审核过期。返修只处理上轮 criterion 问题，尊重人工区域，不静默合并概念或修改稳定 ID。

一概念一卡：10_literature/concepts/<slug>.md，定义是项目内全局唯一来源；论文 analysis 只记录局部用法。
front matter 包含 concept_id、aliases、type、status、first_defined_in、first_seen_year、prerequisites、related、contrasts、papers 和生成来源信息。
type 为 foundational/classic/current/emerging，status 为 not-started/learning/understood/needs-review。
正文十节：一句话定义、为什么需要、直观理解、形式化定义、公式符号、前因后果、相近概念区别、误区、代表文献迷你综述、开放问题。
新概念说明替代/修正什么，旧概念说明为何仍重要。链接相关本地论文和概念；未获取的文献写 TODO(user)。
只建立有来源支持的前置/继承/对比关系，继承/替代说明写正文，并用统一 links 关联；INDEX.json 是机器定位入口，不维护另一份手工 registry。
知识网络用 wf.py index/graph 从本地可追溯数据重建知识地图和 knowledge-graph.json。高频按不同论文数计，Jaccard/IDF、第一性原理和综述比较只给候选；前置顺序按声明图排序，聚类为连通组，中介中心性只是导航指标。不得把统计关系冒充科学结论。
knowledge-builder 未配置或禁用时自动回退到 literature-reader，实际执行角色记入 .runs。

literature-learning-guide 生成论文自己的 06_synthesis/concept-guide.md，遵守该任务合同与 workflow/study-guide.md 的十节结构。先说明光/物质/信息等底层原理，再按真实前置关系解释概念、公式、器件或方法，最后对照论文图表和证据；每个重要概念给定义、为什么需要、假设与边界、在本文的角色、常见误区及学习链接。数值例题写出单位和假设，不能把教学模型冒充论文推导。新概念和旧概念的区别按文献史核对，不按名称新旧猜测。
高频明确统计范围：本文词频、项目不同论文覆盖数和学习优先级分别标注；没有统计结果时不编造次数或领域排名。代表文献区分综述、经典、课题组近期工作，标记全文/摘要/仅书目核对范围。概念全局定义仍在卡中，指南只做教学串联，重要新增概念须由执行器另派 literature-knowledge 更新卡与 analysis。材料缺口显式保留，不能写成“已全面阅读”。

全局卡增加 is_first_principle、canonical_statement、extends、replaces；论文局部第一性原理与综述比较写 04_analysis/analysis.yaml，不复制全局定义。每条边附证据/权重/置信度；自动相似与共现只能是 candidate，核验后才标 verified，建议记录审核者与时间。知识地图人工内容写在 GENERATED 标记之外，不静默合并概念。
