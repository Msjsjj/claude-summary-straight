#!/usr/bin/env python3
"""
对编号列表稳健重编号（v0.4 新增辅助工具）

当某一章节的编号列表中删除了若干条目，剩余条目编号不连续时使用。
本工具不依赖被删条目的位置，按现有条目出现顺序统一重编号为 1, 2, 3, ...

用法：
    python3 renumber_list.py <markdown_file> <chapter_number>

例如：删除"# 8. 对照清单"里的第 4 条后调用
    python3 renumber_list.py /tmp/notion_draft.md 8

实现要点：
- 只在指定一级章节范围内重编号（避免误改其他章节）
- 按行扫描：行首匹配 `<number>. ` 的行视为列表项起始；其后续未编号行（缩进/续行）一并归属此条
- 重新顺序赋号 1, 2, 3, ...
- 章节前置说明文本（如"下面 N 条..."）若包含具体数字，本工具不修正，由调用方自查
"""
import sys
import re
from pathlib import Path


CHAP_HEADING = re.compile(r"(?m)^# (\d+)\. ")


def renumber_chapter(text, chapter_num):
    """在指定章节范围内对所有顶层编号列表项重编号 1..N。"""
    headings = list(CHAP_HEADING.finditer(text))
    if not headings:
        return text

    target_start = None
    target_end = len(text)
    for i, m in enumerate(headings):
        if m.group(1) == chapter_num:
            target_start = m.end()
            if i + 1 < len(headings):
                target_end = headings[i + 1].start()
            break

    if target_start is None:
        sys.stderr.write(f"chapter #{chapter_num} not found\n")
        return text

    body = text[target_start:target_end]

    counter = [0]
    def repl(m):
        counter[0] += 1
        return f"{counter[0]}. "

    new_body = re.sub(r"(?m)^\d+\. ", repl, body)
    return text[:target_start] + new_body + text[target_end:]


def main():
    if len(sys.argv) != 3:
        print("Usage: renumber_list.py <markdown_file> <chapter_number>", file=sys.stderr)
        sys.exit(2)

    md_path = Path(sys.argv[1])
    chap_num = sys.argv[2]
    text = md_path.read_text(encoding="utf-8")
    new_text = renumber_chapter(text, chap_num)
    md_path.write_text(new_text, encoding="utf-8")
    print(f"renumbered chapter #{chap_num} in {md_path}")


if __name__ == "__main__":
    main()
