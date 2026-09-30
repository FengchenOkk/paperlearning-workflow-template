# 第三方依赖

这里只保存第三方技能，项目自己的流程、提示与模板放 workflow 对应目录。不要直接改写第三方文件；本项目的适配规则记录在 workflow 文档和 prompts 中。

## Academic Research Suite

- 原作者：Cheng-I Wu（吳政宜），GitHub 用户名 Imbad0202。
- 下载仓库：https://github.com/Imbad0202/academic-research-skills-codex
- 下载路径：skills/academic-research-suite，main 分支。
- 本地入口：academic-research-suite/SKILL.md。
- 本地适配器版本：3.22.2。
- 下载日期：2026-09-30。
- 使用范围：文献研究与综合的流程参考；尚未注册全局技能或自动启用流水线。

具体上游版本和提交以包内 `manifest.json` 为唯一依据，不在本文件复制提交编号。下载时没有保存 Codex 适配仓库的精确提交，不能声称是已固定提交的下载。

许可证和署名见包内 `ars/LICENSE`、`ars/LICENSE.academic-research-skills`、`ars/NOTICE.md`；使用和分发需保留这些文件。

## 更新记录

| 日期 | 操作 | 说明 |
|---|---|---|
| 2026-09-30 | 下载 | Codex 版 v3.22.2，完整配套文件保留 |
| 2026-09-30 | 结构整理 | 归入 vendor；新增本导航，第三方源码未修改 |

未来更新先核对来源与许可，记录新旧版本和本地适配影响，再替换；不要自动运行第三方脚本或覆盖研究项目。
