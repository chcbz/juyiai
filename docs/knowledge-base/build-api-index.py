#!/usr/bin/env python3
"""Build the compact Controller index from the generated API inventory."""

import argparse
from collections import Counter
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "04-backend-api-inventory.md"
TARGET = HERE / "04-backend-api-index.md"
BASELINE = HERE / "BASELINE.yaml"

HEADING_RE = re.compile(r"^## `(?P<controller>[^`]+Controller)`\s*$", re.MULTILINE)
SOURCE_RE = re.compile(r"^- 源码：\[`(?P<source>[^`]+)`\]\([^)]+\)\s*$", re.MULTILINE)
MAPPING_RE = re.compile(r"^- 类级映射：`(?P<mapping>[^`]+)`\s*$", re.MULTILINE)


def baseline_integer(key):
    pattern = re.compile(r"^\s*{}:\s*(\d+)\s*$".format(re.escape(key)), re.MULTILINE)
    match = pattern.search(BASELINE.read_text(encoding="utf-8"))
    if not match:
        raise RuntimeError("missing integer in BASELINE.yaml: {}".format(key))
    return int(match.group(1))


def markdown_anchor(controller, occurrence):
    base = controller.lower().replace("_", "-")
    return base if occurrence == 0 else "{}-{}".format(base, occurrence)


def inventory_sections(text):
    headings = list(HEADING_RE.finditer(text))
    expected = baseline_integer("controller_files")
    if len(headings) != expected:
        raise RuntimeError(
            "Controller heading count {} does not match BASELINE.yaml {}".format(
                len(headings), expected
            )
        )

    sections = []
    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[start:end]
        source_matches = SOURCE_RE.findall(body)
        mapping_matches = MAPPING_RE.findall(body)
        controller = heading.group("controller")
        if len(source_matches) != 1 or len(mapping_matches) != 1:
            raise RuntimeError(
                "expected one source and one class mapping for {} (sources={}, mappings={})".format(
                    controller, len(source_matches), len(mapping_matches)
                )
            )
        sections.append((controller, source_matches[0], mapping_matches[0]))
    return sections


def render():
    text = SOURCE.read_text(encoding="utf-8")
    sections = inventory_sections(text)
    seen = Counter()
    rows = []

    for controller, source, mapping in sections:
        parts = source.split("/")
        domain = parts[1] if len(parts) > 2 and parts[0] == "api" else "other"
        module = parts[2] if len(parts) > 3 and parts[0] == "api" else "—"
        occurrence = seen[controller]
        seen[controller] += 1
        rows.append(
            (domain, module, controller, mapping, markdown_anchor(controller, occurrence))
        )

    output = [
        "# 后端 API 快速索引",
        "",
        "本页用于先定位领域、模块、Controller 和类级路径；只有在需要逐方法 mapping、源码行号或 `@PreAuthorize` 时，才读取[完整静态清单](04-backend-api-inventory.md)的对应段落。",
        "",
        "当前索引覆盖 **{}** 个 Controller。生成基线见 [`BASELINE.yaml`](BASELINE.yaml)。本文件由 [`build-api-index.py`](build-api-index.py) 确定性生成。".format(len(rows)),
        "",
        "| 领域 | 模块 | Controller | 类级映射 | 完整段落 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for domain, module, controller, mapping, anchor in rows:
        output.append(
            "| `{}` | `{}` | `{}` | `{}` | [查看](04-backend-api-inventory.md#{}) |".format(
                domain, module, controller, mapping, anchor
            )
        )
    output += [
        "",
        "## 使用方式",
        "",
        "```bash",
        "./docs/knowledge-base/kb-search.sh --api AgentController",
        "python3 docs/knowledge-base/build-api-index.py --check",
        "python3 docs/knowledge-base/build-api-index.py",
        "```",
        "",
        "若按基础路径、方法名或权限检索，直接对完整清单执行定向 `rg`，不要先读取整个文件。",
    ]
    return "\n".join(output) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the checked-in index is stale")
    args = parser.parse_args()
    try:
        generated = render()
    except (OSError, RuntimeError, UnicodeError) as exc:
        print("cannot build API index: {}".format(exc), file=sys.stderr)
        return 1
    if args.check:
        if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != generated:
            print("stale generated index: {}".format(TARGET), file=sys.stderr)
            return 1
        print("current: {}".format(TARGET))
        return 0
    TARGET.write_text(generated, encoding="utf-8")
    print("wrote: {}".format(TARGET))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
