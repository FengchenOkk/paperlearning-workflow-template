# 项目文件说明

本目录对应一个研究方向。论文材料和所有论文级分析必须放进该篇论文自己的目录：`10_literature/papers/<citekey>/`。

```text
<research-slug>/
├── project.yaml                     # 项目阶段、当前主张和复现扩展配置
├── research-profile.yaml            # 研究目标、资源、约束和路线偏好
├── README.md                        # 本文件；目录与文件职责说明
├── INDEX.md                         # 面向人的项目导航，由工具更新
├── INDEX.json                       # 面向程序的稳定 ID、路径、哈希和任务状态
├── 00_inbox/                        # 尚未归档的资料和任务包
├── 10_literature/
│   ├── README.md                    # 文献区使用说明
│   ├── reading-list.md              # 跨论文阅读顺序和阅读理由
│   ├── matrix.md                    # 跨论文对比矩阵，人工维护
│   ├── knowledge-map.md             # 面向人的知识关系图
│   ├── knowledge-graph.json         # 面向程序的知识图谱，由工具生成
│   ├── concepts/                    # 项目共享概念卡，一概念一文件
│   └── papers/
│       └── <citekey>/               # 一篇论文一个独立目录
│           ├── meta.yaml            # 论文身份、来源、状态和下一步
│           ├── 01_source/           # 原文、附件和来源链接；原始资料只读
│           ├── 02_translation/
│           │   └── translation.md   # 按原文章节和段落追加的翻译
│           ├── 03_reading/
│           │   └── reading.md       # 全局定位、逐节精读和证据索引
│           ├── 04_analysis/
│           │   └── analysis.yaml    # 公式、概念、主张、方法和复现线索
│           └── 05_notes/
│               └── notes.md         # 临时疑问和灵感，不作为正式结论
├── 20_reproduction/
│   └── <citekey>--<claim-slug>/      # 一项可检验主张一个目录
│       ├── claim.yaml                # 主张身份、资源、路线、标准和状态
│       ├── feasibility.md            # 可行性与资源缺口
│       ├── plan.md                   # 复现计划、依赖和里程碑
│       ├── online/                   # 代码、模拟和线上实验
│       ├── lab/                      # 线下实验协议和记录
│       └── results/                  # 实际结果、图表和日志
└── 30_outputs/                       # 经过核验的报告和交付成果
```

维护原则：论文状态只写 `meta.yaml`，项目阶段只写 `project.yaml`，复现状态只写 `claim.yaml`。`INDEX.md`、`INDEX.json` 和 `knowledge-graph.json` 可重新生成；`matrix.md` 与生成标记之外的人工内容会保留。正式成果进入 `30_outputs/`，模型草稿保存在 `.runs/`，不直接混入正式内容。
