#!/usr/bin/env python3
"""
post_check.py: Summary-straight 笔记质量检查（写入后运行）

检查项：
  1. external_urls   - 外部来源链接（web search 已执行的证据）
  2. example_present - 例题存在（含"例题"关键词）
  3. frontmatter     - 必填字段（date / course / chapter / status）
  4. wikilink        - WikiLink 联结存在（[[...]] 语法）

用法：
    python post_check.py <file.md>

返回：
    JSON 格式报告，stdout 输出。
    退出码：全部通过 -> 0；任一失败 -> 1。
"""

import sys
import re
import json


def read_discipline(content):
    m = re.search(r'^discipline\s*:\s*(\S+)', content, re.MULTILINE)
    if m:
        val = m.group(1).split('#')[0].strip()
        if val in ('stem', 'law', 'politics'):
            return val
    return None


def check_external_urls(content):
    # 去掉 frontmatter，只检查正文
    body = re.sub(r'^---.*?^---\s*', '', content, count=1, flags=re.DOTALL | re.MULTILINE)
    urls = re.findall(r'\[[^\]]+\]\(https?://[^\)]+\)', body)
    return {
        "check": "external_urls",
        "description": "笔记正文应含外部来源链接（web_search 已执行的证据）",
        "passed": len(urls) > 0,
        "found": len(urls),
        "tip": "未发现外部链接。请执行 web_search（课程名+章节+期末重点/考研真题），并在复习定位节引用来源 URL。"
    }


def check_example_present(content, discipline=None):
    # 检查正式例题段落：**例题** 加粗格式，而非散文中偶然出现的"例题"二字
    has = bool(re.search(r'\*\*例题\*\*', content))
    tips = {
        'stem':     "未发现正式例题。计算类章节（银行家算法、页面置换等）必须含 **例题** 加粗段落；描述类章节也应提供典型场景案例。",
        'law':      "未发现正式例题。法学章节应含 **例题** 加粗段落，覆盖案例分析题（效力/责任判断或制度区分），骨架复用正文要件清单与对比表。",
        'politics': "未发现正式例题。政治章节应含 **例题** 加粗段落，覆盖高频简答/论述题，骨架从该知识点自身结构展开。",
    }
    tip = tips.get(discipline, "未发现正式例题。笔记应含 **例题** 加粗段落，覆盖本章核心考点。")
    return {
        "check": "example_present",
        "description": "笔记应含正式例题（**例题** 加粗格式）",
        "passed": has,
        "tip": tip
    }


def check_frontmatter(content):
    required = ["date", "course", "chapter", "status"]
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        return {
            "check": "frontmatter",
            "description": "frontmatter 应包含 date / course / chapter / status",
            "passed": False,
            "missing_fields": ["frontmatter 完全缺失"]
        }
    fm_body = fm_match.group(1)
    missing = [f for f in required if not re.search(rf'^{f}\s*:', fm_body, re.MULTILINE)]
    return {
        "check": "frontmatter",
        "description": "frontmatter 应包含 date / course / chapter / status",
        "passed": len(missing) == 0,
        "missing_fields": missing
    }


def check_wikilink(content):
    links = re.findall(r'\[\[.+?\]\]', content)
    return {
        "check": "wikilink",
        "description": "笔记应含 WikiLink 联结相关章节",
        "passed": len(links) > 0,
        "found": len(links),
        "tip": "未发现 WikiLink。请在正文中用 [[笔记名]] 链接同课程的相关章节笔记。"
    }


def run(path):
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return {"error": "File not found: " + path}
    except Exception as e:
        return {"error": str(e)}

    discipline = read_discipline(content)
    checks = [
        check_external_urls(content),
        check_example_present(content, discipline),
        check_frontmatter(content),
        check_wikilink(content),
    ]
    failed = [c for c in checks if not c["passed"]]
    return {
        "overall_passed": len(failed) == 0,
        "failed_checks": [c["check"] for c in failed],
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python post_check.py <file.md>")
        sys.exit(1)
    result = run(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("overall_passed", False) else 1)
