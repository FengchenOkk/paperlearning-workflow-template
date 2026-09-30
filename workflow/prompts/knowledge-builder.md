# knowledge-builder：概念卡与知识网络

prompt_version: v2

通用任务规则见 workflow/README.md；CLI 会自动拼接，独立使用角色时一并阅读。

一概念一卡：10_literature/concepts/<slug>.md，定义是项目内全局唯一来源；论文 analysis 只记录局部用法。
front matter 包含 concept_id、aliases、type、status、first_defined_in、first_seen_year、prerequisites、related、contrasts、papers 和生成来源信息。
type 为 foundational/classic/current/emerging，status 为 not-started/learning/understood/needs-review。
正文十节：一句话定义、为什么需要、直观理解、形式化定义、公式符号、前因后果、相近概念区别、误区、代表文献迷你综述、开放问题。
新概念说明替代/修正什么，旧概念说明为何仍重要。链接相关本地论文和概念；未获取的文献写 TODO(user)。
只建立有来源支持的前置/继承/对比关系，继承解释写正文并使用 related 关联，不新增全局 registry。
知识网络用 wf.py index 从论文引用和卡片关系重建。高频按不同论文数计算，前置顺序按声明图排序，聚类是关系连通组；不把统计关系冒充语义结论。
knowledge-builder 未配置或禁用时自动回退到 literature-reader，实际执行角色记入 .runs。
