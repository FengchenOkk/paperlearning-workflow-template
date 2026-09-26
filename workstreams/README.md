# 工作流目录

每个独立研究课题占用一个目录。`workstreams/WS-*/` 默认被忽略，用来保存每位使用者自己的私有科研实例：

```text
workstreams/
└── WS-002-example/
    ├── README.md       # 目标、范围、任务和完成标准
    ├── notes/          # 过程笔记
    ├── src/            # 代码，可按需要创建
    └── results/        # 中间结果，可按需要创建
```

创建新工作流：

```powershell
node planning/scripts/new-workstream.mjs WS-001 example-topic "示例课题"
```

如果你希望公开某个示例，不要直接取消整个 `WS-*` 忽略规则；应复制并脱敏为单独的 `examples/` 内容。
