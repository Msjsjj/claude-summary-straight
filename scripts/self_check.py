#!/usr/bin/env python3
"""
Obsidian 笔记自检脚本（v0.5 - Obsidian 版）

对写入 Vault 后的笔记进行三项硬约束检查：

1. 章节编号连续性（阿拉伯数字 + 中文数字编号都不能跳号）
2. 元规则泄漏检查（"公式书写规范"等工作流元信息混入笔记正文）
3. 收尾板块数量检查（≤ 2 个）

注：原 Notion 版的公式渲染失败检查（\\$ 检测）已移除——
Obsidian 本地文件无需 fetch，也不存在 \\$ 转义问题。

用法：
    python3 self_check.py <markdown_file>

返回：
    JSON 格式的报告，stdout 输出。
    退出码：全部通过 → 0；任一失败 → 1。
"""

import sys
import re
import json
import argparse


def check_section_numbering(content: str) -> dict:
    """检查章节编号是否连续。

    支持两种编号风格：
    - 阿拉伯数字：# 1. 标题 / ## 1.1 子标题
    - 中文数字：# 一、标题 / ## 二、标题

    只检查顶级编号的连续性。
    """
    arabic_pattern = r'^#\s+(\d+)\.\s'
    arabic_numbers = []
    for line in content.split('\n'):
        m = re.match(arabic_pattern, line)
        if m:
            arabic_numbers.append(int(m.group(1)))

    arabic_violation = None
    if arabic_numbers:
        expected = list(range(1, max(arabic_numbers) + 1))
        if arabic_numbers != expected:
            arabic_violation = {
                "actual": arabic_numbers,
                "expected": expected,
                "missing": [n for n in expected if n not in arabic_numbers],
                "duplicate": [n for n in arabic_numbers if arabic_numbers.count(n) > 1],
            }

    cn_digits = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    }
    cn_pattern = r'^#\s+([一二三四五六七八九十]+)、\s'
    cn_numbers = []
    for line in content.split('\n'):
        m = re.match(cn_pattern, line)
        if m:
            char = m.group(1)
            if char in cn_digits:
                cn_numbers.append(cn_digits[char])

    cn_violation = None
    if cn_numbers:
        expected = list(range(1, max(cn_numbers) + 1))
        if cn_numbers != expected:
            cn_violation = {
                "actual": cn_numbers,
                "expected": expected,
                "missing": [n for n in expected if n not in cn_numbers],
                "duplicate": [n for n in cn_numbers if cn_numbers.count(n) > 1],
            }

    passed = arabic_violation is None and cn_violation is None
    return {
        "check": "section_numbering",
        "description": "章节编号连续性检查",
        "passed": passed,
        "arabic_violation": arabic_violation,
        "chinese_violation": cn_violation,
    }


def check_meta_rules_leak(content: str) -> dict:
    """检查工作流元规则是否混入笔记正文。"""
    leak_indicators = [
        "公式书写规范",
        "公式书写规则",
        "数学公式统一",
        "数学公式规则",
        "独立公式：用 LaTeX",
        "本 skill",
        "工作流",
        "Markdown shortcut",
    ]

    leaks = []
    for indicator in leak_indicators:
        idx = 0
        while True:
            pos = content.find(indicator, idx)
            if pos == -1:
                break
            start = max(0, pos - 30)
            end = min(len(content), pos + len(indicator) + 30)
            leaks.append({
                "term": indicator,
                "context": content[start:end].replace('\n', ' '),
                "position": pos,
            })
            idx = pos + len(indicator)

    return {
        "check": "meta_rules_leak",
        "description": "工作流元规则泄漏检查",
        "passed": len(leaks) == 0,
        "leak_count": len(leaks),
        "leaks": leaks,
    }


def check_closing_blocks(content: str) -> dict:
    """检查收尾板块数量是否超标（> 2×N 视为不合格，N 为节数）。

    多节合一文件按节缩放收尾板块上限，单节文件 N=1 行为不变。
    """
    closing_indicators = [
        "易错点", "考前速记", "最小复习清单", "高频题型",
        "复习顺序", "建议复习顺序", "关键参数", "总结归纳",
        "知识地图", "速记卡",
    ]

    # 多节合一文件按节缩放收尾板块上限，单节文件 N=1 行为不变
    # 匹配 ## 第X节 或 ## [预留] 第X节 形式的二级节标题（预留节也计入）
    section_re = re.compile(r'^##\s+(?:\[.*?\]\s*)?第[一二三四五六七八九十百千]+节')
    n_sections = sum(1 for line in content.split('\n') if section_re.match(line.strip()))
    if n_sections == 0:
        n_sections = 1
    limit = 2 * n_sections

    found_headings = []
    lines = content.split('\n')
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith('#'):
            for indicator in closing_indicators:
                if indicator in line_stripped:
                    found_headings.append(line_stripped)
                    break

    return {
        "check": "closing_blocks_count",
        "description": f"收尾板块数量检查（≤ {limit}，文件含 {n_sections} 节）",
        "passed": len(found_headings) <= limit,
        "count": len(found_headings),
        "limit": limit,
        "n_sections": n_sections,
        "found": found_headings,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Obsidian 笔记自检脚本（v0.5）",
    )
    parser.add_argument(
        "markdown_file",
        help="已写入 Vault 的笔记文件路径",
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
        check_section_numbering(content),
        check_meta_rules_leak(content),
        check_closing_blocks(content),
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
