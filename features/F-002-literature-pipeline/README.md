# F-002 文献精读与知识框架流水线

## 目的

把 Zotero 中的论文变成可追踪、可复核的阅读包，并为各研究工作流提供统一的双语翻译、精读、证据、概念和关联文献记录。Zotero 管理论文原件、主书目数据、集合和批注；本功能管理研究过程与产物。

Zotero 连接、集合映射和元数据同步由 [`F-003`](../F-003-zotero-bridge/README.md) 负责。两者分开是为了让“外部文献库接入”与“如何精读一篇论文”各自保持单一职责。

## 状态流

```text
Zotero mapped collection → 10-queue → 20-active → 30-review → 40-library/<topic>
                                                    └────────→ 90-hold
```

- `00-index`：Zotero 映射集合的生成式目录，不是投递箱。
- `10-queue`：同步发现的新条目，已生成模板，尚未精读。
- `20-active`：Codex 已认领并正在翻译/分析；一次只处理少量论文。
- `30-review`：初稿完成，等待来源、数字、图表和术语核验。
- `40-library/<topic>`：通过 Codex 终审的阅读成果；论文原件仍留在 Zotero。
- `90-hold`：无全文、版本不明、损坏或暂缓材料；必须记录原因。

目录位置表达主状态，`manifest.json` 保存机器可读状态；Zotero collection 只表达研究主题。阶段迁移由 Codex 在检查交付物后执行。

## 从 Zotero 开始

1. 在 Zotero 中建立完整的父条目，补齐标题、作者、年份、DOI/URL，并附 PDF。
2. 把父条目放进一个或多个已映射集合。
3. 保持 Zotero 桌面端运行，执行 `npm run zotero:sync` 或双击根目录 `sync-zotero.cmd`。
4. 在 Codex 中指定 Zotero item key、标题或优先研究方向。

同步不会复制 PDF，也不会改写 Zotero。Codex 通过 `research/literature/.local/zotero-resolved.json` 定位本机附件；该文件不提交版本库。

## 每篇论文的最小交付物

| 文件 | 内容与质量门槛 |
| --- | --- |
| `manifest.json` | Zotero item/attachment key、集合映射、状态和元数据快照；不保存本机绝对路径 |
| `00-status.md` | 当前进度、负责人、下一动作、阻塞项、DSH 参与记录 |
| `01-bibliography.md` | 标题、作者、年份、期刊/会议、DOI/URL、版本关系及逐项核验状态 |
| `02-translation.md` | 结构化的原文—中文对应段，带页码/图表锚点；是翻译内容的主文件 |
| `02-translation.html` | 自动生成的左右对照阅读页，可搜索、打印；不直接手工编辑 |
| `03-deep-reading.md` | 研究对象、核心问题、重要性、假设、方法、结果、逻辑链、局限和可迁移启示 |
| `04-evidence.csv` | 每个材料性结论对应原文位置、证据类型、核验状态；观察与推断分开 |
| `05-concepts.md` | 高频概念的定义、先修知识、本文用法、相互关系和未解问题 |
| `06-related-literature.md` | 代表综述、经典论文、课题组近期工作；说明选择理由和关系 |
| `07-review.md` | Codex 终审清单、纠错记录、残余不确定性、是否允许进入正式综合 |
| `08-reader-summary.md` | 面向用户的细致综合，不替代前述可追溯材料 |

## 双语对照阅读

`02-translation.md` 使用以下可重复区块：

```text
<!-- segment
id: introduction-001
heading: Introduction · 1
source: PDF p. 2
-->
::: original
原文段落
:::
::: zh
对应中文
:::
```

更新后渲染：

```powershell
npm run literature:render -- "research/literature/20-active/<paper>/02-translation.md"
```

本机 `npm` 启动器不可用时，使用：

```powershell
node features/F-002-literature-pipeline/scripts/render-translation.mjs "research/literature/20-active/<paper>/02-translation.md"
```

`02-translation.html` 在宽屏上左右并排，在窄屏上上下排列。每段独立锚定，可直接对照 PDF 页码。

## 模型分工与质量门槛

Codex/GPT 主责研究问题、全文逻辑、关键公式/图表、方法有效性、来源核验和最终综合。DSH 只在任务边界清楚时承担候选提取、结构清晰段落的翻译初稿、格式缺项检查或独立质疑；其引文、数字和结论均须回到原始来源核验。

进入 `40-library` 前至少满足：PDF 可访问；元数据及版本关系核验；翻译覆盖范围明确；关键结论进入证据表；数字、单位、图表和术语已抽查；残余不确定性写入终审；HTML 与 Markdown 的分段数一致。

## 验证

```powershell
npm run literature:test
npm run zotero:check
```

模板自动测试覆盖 Zotero 元数据和 PDF 路径解析、稳定 item key 去重、无源文件副本的阅读包、重复同步、双语段落解析和左右对照 HTML。每位使用者仍需用自己的真实论文验收全文提取、扫描型 PDF、补充材料配对和长篇分批翻译。
