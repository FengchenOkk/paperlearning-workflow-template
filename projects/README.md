# 研究项目目录

这里仅保存真实研究项目，不放示例项目或项目模板。一个研究方向对应一个目录：

```text
projects/
└── <research-slug>/
    ├── project.yaml
    ├── research-profile.yaml
    ├── README.md
    ├── INDEX.md
    ├── INDEX.json
    ├── 00_inbox/
    ├── 10_literature/
    ├── 20_reproduction/
    └── 30_outputs/
```

创建研究项目：

```powershell
python tools/wf.py init <research-slug> --title "研究方向名称"
```

创建论文目录：

```powershell
python tools/wf.py new paper <research-slug> <citekey>
```

每篇论文都会保存到 `10_literature/papers/<citekey>/`，原文、翻译、精读、结构化分析和临时笔记均位于该论文自己的目录中。项目内完整文件清单和用途见生成项目中的 `README.md`。

工作流用于初始化的内部文件定义位于 `workflow/layouts/`，不属于研究数据，也不会作为项目出现在这里。
