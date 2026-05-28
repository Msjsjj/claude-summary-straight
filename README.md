# Summary-straight · Claude Code Skill

一个 Claude Code skill，把课程 PPT / PDF / Word 自动整理成结构化的 Obsidian 期末复习笔记。

## 效果

- 自动识别章节、定位课程文件夹
- 格式选择有规则（参数表格 / ASCII 流程图 / 对比表 / Mermaid 拓扑图……）
- 搜集外部例题，必写"考试考向与例题"板块
- 写入前跑 `pre_check`，写入后跑 `self_check` + `post_check`，三道关卡保证质量
- 支持两种模式：上传资料 / 只告诉课程名+章节

## 前置要求

- [Claude Code](https://claude.ai/code)（CLI 或桌面版均可）
- Python 3.8+
- Obsidian（Vault 下需有 `Summary-straight/` 文件夹，课程子文件夹自建）

## 安装

```bash
# 把整个文件夹复制到 Claude Code 的 skills 目录
# Windows
xcopy /E /I summary-straight "%USERPROFILE%\.claude\skills\summary-straight"

# macOS / Linux
cp -r summary-straight ~/.claude/skills/summary-straight
```

重启 Claude Code，skill 即生效。

## 用法

在 Claude Code 对话框输入触发词即可：

```
/summary-straight
```

**有源资料（推荐）**：上传 PPT / PDF / Word 后说"帮我整理成复习笔记"

**无源资料**：直接说课程名和章节，skill 会反问教材版本，然后联网检索内容

## 文件结构

```
summary-straight/
├── SKILL.md          # skill 主配置（Claude Code 读取）
└── scripts/
    ├── pre_check.py      # 写入前：检查 LaTeX 公式合法性
    ├── self_check.py     # 写入后：章节编号、元规则泄漏、收尾板块数量
    ├── post_check.py     # 写入后：例题、外链、frontmatter、WikiLink
    ├── fix_bold.py       # 辅助工具：按章节精简加粗
    └── renumber_list.py  # 辅助工具：编号列表重编号
```

## Vault 目录约定

skill 会在你的 Vault 下寻找 `Summary-straight/<课程名>/` 文件夹写入笔记。首次使用前手动建好课程文件夹即可，例如：

```
Obsidian Vault/
└── Summary-straight/
    ├── 操作系统/
    ├── 应用密码学/
    └── 计算机网络/
```

## License

MIT
