# 公共模板发布检查

本仓库采用“公共工作流模板 + 本机私有科研实例”结构。`.gitignore` 负责阻止个人研究内容进入公共仓库，但首次推送前仍必须人工检查暂存区。

## 应公开

- `README.md`、`AGENTS.md`、`LICENSE`；
- `PROJECT.example.md` 和 `planning/*.example.md`；
- `features/` 下的通用脚本、模板、测试和说明；
- `collections.example.json`；
- `research/`、`outputs/`、`workstreams/` 的说明文件；
- `package.json`、锁文件和通用入口脚本。

## 应保持本机私有

- `PROJECT.md`、`planning/BACKLOG.md`、`DECISIONS.md`、`ROADMAP.md`；
- `workstreams/WS-*/`；
- 实际 `outputs/`、`research/` 内容和 Zotero 阅读包；
- `collections.local.json`、`.env`、PDF、大型数据；
- DSH 任务、模型运行记录和本机路径。

## 首次提交前

初始化 Git 后先运行：

```powershell
git add .
git status --short
git status --ignored --short
git diff --cached --stat
```

确认暂存区没有上述私有内容。还可以检查敏感类型：

```powershell
git diff --cached --name-only | Select-String -Pattern '\.env$|\.pdf$|collections\.local\.json|zotero-resolved|\.runtime|workstreams/WS-'
```

正常情况下该命令不应输出任何路径。若出现私有文件：

```powershell
git restore --staged "文件路径"
```

然后先修正 `.gitignore`，再重新暂存。推送到 GitHub 后还应在网页上复查一次文件列表。

## 许可边界

通用代码和模板使用 MIT License。论文、出版物图表、第三方数据、完整翻译和其他不属于贡献者的材料不因本许可证而获得重新分发许可；这些内容默认不进入公共仓库。
