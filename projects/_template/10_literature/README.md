# 文献导航

- papers/<citekey>/：入口 meta.yaml；01_source 原文、02_translation 翻译、03_reading 精读、04_analysis 分析、05_notes 临时笔记。
- concepts/<slug>.md：项目内全局概念卡，一个概念一张卡。
- reading-list.md：阅读路径与理由；身份、类别、优先级和状态从 meta.yaml 生成。
- matrix.md：跨论文比较，手工维护，不被 index 覆盖。
- knowledge-map.md 与 knowledge-graph.json：index/graph 生成的本地知识网络；自动相似关系有证据，待主模型核验，人工内容放生成标记之外。
- 项目根 INDEX.md：自动分类、时间线、复现 claim 和成果导航。

顺序：入库分类 → 全局预读 → 分段翻译与精读 → 公式概念 → 上下文 → 知识网络 → 核验综合。
文献综合工作稿按需写在本目录的具名 Markdown 文件中；不再预建 synthesis/。核验后的交付快照放 30_outputs/。

可选 Zotero 入库见 workflow/zotero.md；旧论文先用 migrate --dry-run 预览，再安全复制迁移。模型分工独立配置，Zotero 不可用时仍可手动阅读。
