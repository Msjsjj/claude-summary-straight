#!/usr/bin/env python3
"""
Obsidian 笔记预检脚本（v0.6 - 精简版）

在写入 Vault 之前对 markdown 草稿做 1 项检查：

1. 行内公式合法性——形如 `$x = $`、`$ = y$` 等"等号一侧空"的公式会渲染失败。

已移除的检查（原 Notion 版）：
- 加粗密度 / 整段加粗 / 整行列表项加粗
- 小标签密度（如 X：）
- 单个加粗内容长度
- 公式边界 / 列表项公式 / 空引用块

用法：
    python3 pre_check.py <markdown_file>

返回：
    JSON 报告（stdout）+ 退出码（全部通过 0，任一失败 1）。
"""

import sys
import re
import json
import argparse


# -------- 工具函数 --------

def find_inline_math(content):
    """找出所有行内公式的位置和内容。"""
    pattern = r'(?<!\$)\$([^$\n]+)\$(?!\$)'
    return [(m.start(), m.end(), m.group(1), m.group(0))
            for m in re.finditer(pattern, content)]


# -------- 检查 --------

def check_inline_formula_validity(content):
    """检查：行内公式内容是否合法 LaTeX。

    形如 `$d = $`、`$x = $`、`$ = y$` 这种"等号一侧空"的公式会渲染失败。
    """
    violations = []
    for start, end, inner, full in find_inline_math(content):
        stripped = inner.strip()
        bad = False
        if re.match(r'^[a-zA-Z_0-9^{}\\]*\s*=\s*$', stripped):
            bad = True  # 形如 "x = "
        elif re.match(r'^\s*=\s*[a-zA-Z_0-9^{}\\]*$', stripped):
            bad = True  # 形如 " = y"
        elif stripped in ('=', '+', '-', '*', '/'):
            bad = True  # 只有运算符
        if bad:
            ctx_start = max(0, start - 20)
            ctx_end = min(len(content), end + 20)
            ctx = content[ctx_start:ctx_end].replace('\n', ' ')
            violations.append({
                "formula": full,
                "issue": "等号一侧或两侧无内容，非合法 LaTeX",
                "context": ctx,
                "position": start,
            })
    return {
        "check": "inline_formula_validity",
        "description": "行内公式内容必须是合法 LaTeX 表达式",
        "passed": len(violations) == 0,
        "violation_count": len(violations),
        "violations": violations[:10],
    }


# -------- 主程序 --------

def main():
    parser = argparse.ArgumentParser(description="Obsidian 笔记预检脚本（v0.6）")
    parser.add_argument(
        "markdown_file",
        help="markdown 草稿文件路径（写入 Vault 之前）",
    )
    args = parser.parse_args()

    try:
        with open(args.markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(json.dumps({
            "error": f"File not found: {args.markdown_file}",
        }, ensure_ascii=False, indent=2))
        sys.exit(2)
    except Exception as e:
        print(json.dumps({
            "error": f"Failed to read file: {e}",
        }, ensure_ascii=False, indent=2))
        sys.exit(2)

    checks = [
        check_inline_formula_validity(content),
    ]

    all_passed = all(c["passed"] for c in checks)
    failed_checks = [c["check"] for c in checks if not c["passed"]]

    report = {
        "overall_passed": all_passed,
        "failed_checks": failed_checks,
        "checks": checks,
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
