#!/usr/bin/env python3
"""
按章节削减加粗（v0.4 新增辅助工具）

当 pre_check 报告 bold_density 超标时使用。
不重写笔记内容，只把不在 KEEP 集合里的加粗脱粗。

用法：
    python3 fix_bold.py <markdown_file> <keep_yaml_file>

KEEP 配置文件示例（yaml，无依赖手写解析）：
    2: 商事主体, 营利性, 营业性, 资格性, 独立性, 三大类
    3: 商业名称, 专属性, 人格性, 唯一性
    5: 商事登记, 创设效力, 公示效力, 对抗效力, 公信效力

格式：章节号 + 冒号 + 该章保留的加粗内容（逗号分隔）。
任何一级章节里出现的加粗，只要 inner 文本不在该章 KEEP 列表中，就被脱粗。
未在配置里出现的章节号，按默认 KEEP={} 处理（即该章所有加粗都被脱粗）。
"""
import sys
import re
from pathlib import Path


def parse_keep(path):
    """解析 KEEP 配置 yaml（简化语法，无需 pyyaml）。"""
    keep = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        head, rest = line.split(":", 1)
        chap_num = head.strip()
        items = [x.strip() for x in rest.split(",") if x.strip()]
        keep[chap_num] = set(items)
    return keep


def split_chapters(text):
    """按 ^# N. 标题切分一级章节，返回 [(num, title_line, body), ...]。

    第一个元组的 num 为 'PRE'，对应章节标题之前的内容（如有）。
    """
    parts = re.split(r"(?m)^(# (\d+)\. .*)$", text)
    chapters = []
    if parts and parts[0]:
        chapters.append(("PRE", "", parts[0]))
    for i in range(1, len(parts), 3):
        title = parts[i]
        num = parts[i + 1]
        body = parts[i + 2] if i + 2 < len(parts) else ""
        chapters.append((num, title, body))
    return chapters


def strip_bold_except(body, keep_set):
    """对一段内容里所有 **xxx**，xxx 不在 keep_set 中则脱粗。"""
    def repl(m):
        inner = m.group(1)
        return f"**{inner}**" if inner in keep_set else inner
    return re.sub(r"\*\*([^*\n]+?)\*\*", repl, body)


def main():
    if len(sys.argv) != 3:
        print("Usage: fix_bold.py <markdown_file> <keep_yaml_file>", file=sys.stderr)
        sys.exit(2)

    md_path = Path(sys.argv[1])
    keep = parse_keep(sys.argv[2])

    text = md_path.read_text(encoding="utf-8")
    chapters = split_chapters(text)

    out_parts = []
    report = {}
    for num, title, body in chapters:
        if num == "PRE":
            out_parts.append(body)
            continue
        keep_set = keep.get(num, set())
        new_body = strip_bold_except(body, keep_set)
        out_parts.append(title + new_body)
        # 统计
        bolds_before = re.findall(r"\*\*([^*\n]+?)\*\*", body)
        bolds_after = re.findall(r"\*\*([^*\n]+?)\*\*", new_body)
        report[num] = {"before": len(bolds_before), "after": len(bolds_after)}

    md_path.write_text("".join(out_parts), encoding="utf-8")

    import json
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
