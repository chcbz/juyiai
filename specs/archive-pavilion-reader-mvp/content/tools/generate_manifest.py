#!/usr/bin/env python3
"""Build the byte-addressable Shuihu Zhuan 120-chapter content fixture."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

EDITION_ID = "shuihuzhuan-zh-120-v1"
WORK_ID = "shuihuzhuan"
WORK_TITLE = "水滸傳"
UPSTREAM_REPO = "pondahai/shuihu-wiki"
UPSTREAM_COMMIT = "b8d911354bd4d8f399e140c458853926f6beb875"
SOURCE_SHA256 = "1023e78e50df0b0902b47ea2f29f0901aa14e55b6d243bd1ce8cfa3202440b47"
SOURCE_PAGE = "https://zh.wikisource.org/zh-hant/水滸傳_(120回本)"
REPRESENTATION_SCHEMA_VERSION = 1
LICENSE_NOTICE = "\u3000PublicdomainPublicdomainfalsefalse"
CHINESE_LICENSE_NOTICE = "\u3000此明朝作品在全世界都屬於公有領域，因為作者逝世已經超過100年，且作品於1931年1月1日之前出版。"

_CHINESE_DIGITS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_CHAPTER_RE = re.compile(r"^第([一二三四五六七八九十百]+)回 (.+)$")


class FixtureError(ValueError):
    """Raised when the frozen source does not satisfy the content contract."""


def chinese_number(value: str) -> int:
    if "百" in value:
        head, rest = value.split("百", 1)
        result = (_CHINESE_DIGITS.get(head, 1) if head else 1) * 100
        value = rest
    else:
        result = 0
    if "十" in value:
        head, tail = value.split("十", 1)
        result += (_CHINESE_DIGITS.get(head, 1) if head else 1) * 10
        result += _CHINESE_DIGITS.get(tail, 0)
    elif value:
        result += _CHINESE_DIGITS[value]
    return result


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utf8_byte_length(text: str) -> int:
    return len(text.encode("utf-8"))


def validate_utf8_byte_range(text: str, start_byte: int, end_byte: int) -> str:
    """Return a UTF-8 byte slice, rejecting offsets inside a code point."""
    data = text.encode("utf-8")
    if not isinstance(start_byte, int) or not isinstance(end_byte, int):
        raise FixtureError("UTF-8 byte offsets must be integers")
    if start_byte < 0 or end_byte < start_byte or end_byte > len(data):
        raise FixtureError("UTF-8 byte range is out of bounds")
    try:
        data[:start_byte].decode("utf-8")
        data[:end_byte].decode("utf-8")
        return data[start_byte:end_byte].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FixtureError("UTF-8 byte range does not land on code-point boundaries") from exc


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def block_content_sha256(manifest_sha256: str, block_type: str, block: Dict[str, object]) -> str:
    if block_type == "PREFACE":
        block_id = block["prefaceId"]
    elif block_type == "CHAPTER":
        block_id = block["chapterId"]
    else:
        raise FixtureError(f"unsupported block type: {block_type}")
    lines = [manifest_sha256, block_type, block_id, block["title"]]
    prefix = "\n".join(str(value) for value in lines) + "\n"
    suffix = "".join(
        "%s\t%s\t%d\n" % (paragraph["paragraphId"], paragraph["sha256"], paragraph["utf8ByteLength"])
        for paragraph in block["paragraphs"]
    )
    return sha256_bytes((prefix + suffix).encode("utf-8"))


def catalog_etag(manifest_sha256: str) -> str:
    return 'W/"archive-catalog-json-v%d-%s"' % (REPRESENTATION_SCHEMA_VERSION, manifest_sha256)


def block_etag(manifest_sha256: str, block_type: str, block: Dict[str, object]) -> str:
    digest = block_content_sha256(manifest_sha256, block_type, block)
    return 'W/"archive-block-json-v%d-%s"' % (REPRESENTATION_SCHEMA_VERSION, digest)


def if_none_match_matches(header_value: str, current_etag: str) -> bool:
    """Apply weak If-None-Match comparison for the generated archive ETag."""
    if not isinstance(header_value, str) or not isinstance(current_etag, str):
        raise FixtureError("If-None-Match and current ETag must be strings")
    value = header_value
    if re.fullmatch(r'[ \t]*\*[ \t]*', value):
        return True
    if re.fullmatch(r'[ \t]*', value) or re.search(r',[ \t]*$', value):
        raise FixtureError("malformed If-None-Match")
    token_re = re.compile(r'[ \t]*((?:W/)?"[\x21\x23-\x7e\x80-\xff]*")[ \t]*(?:,|$)')
    tokens = []
    position = 0
    while position < len(value):
        match = token_re.match(value, position)
        if not match:
            raise FixtureError("malformed If-None-Match")
        tokens.append(match.group(1))
        position = match.end()
    if not tokens:
        raise FixtureError("malformed If-None-Match")
    current_opaque = current_etag[2:] if current_etag.startswith("W/") else current_etag
    return any((token[2:] if token.startswith("W/") else token) == current_opaque for token in tokens)


def _paragraph(paragraph_id: str, text: str) -> Dict[str, object]:
    encoded = text.encode("utf-8")
    if not text:
        raise FixtureError(f"empty paragraph: {paragraph_id}")
    return {
        "paragraphId": paragraph_id,
        "text": text,
        "utf8ByteLength": len(encoded),
        "sha256": sha256_bytes(encoded),
    }


def _flush_paragraphs(chapter_id: str, lines: List[str]) -> List[Dict[str, object]]:
    return [_paragraph(f"{chapter_id}-p{index:04d}", line) for index, line in enumerate(lines, 1)]


def _block_utf8_byte_length(paragraphs: List[Dict[str, object]]) -> int:
    return sum(paragraph["utf8ByteLength"] for paragraph in paragraphs)


def parse_source(raw: bytes, expected_sha256: str = SOURCE_SHA256) -> Dict[str, object]:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise FixtureError("UTF-8 BOM is not allowed")
    if b"\r\n" in raw or b"\r" in raw:
        raise FixtureError("CRLF or bare CR is not allowed")
    actual_sha256 = sha256_bytes(raw)
    if expected_sha256 and actual_sha256 != expected_sha256:
        raise FixtureError(f"source SHA-256 mismatch: expected {expected_sha256}, got {actual_sha256}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FixtureError(f"source is not valid UTF-8: {exc}") from exc
    if not raw.endswith(b"\n\n") or raw.endswith(b"\n\n\n"):
        raise FixtureError("source must end with exactly one terminal blank line (two LF bytes)")
    lines = text.split("\n")[:-1]
    preface_lines = []  # type: List[str]
    chapters = []  # type: List[Dict[str, object]]
    current = None  # type: Optional[Dict[str, object]]
    saw_preface = False
    expected_number = 1

    for line_number, line in enumerate(lines, 1):
        if line == "":
            continue
        if line == "引首":
            if saw_preface or chapters or preface_lines:
                raise FixtureError(f"unexpected or duplicate 引首 at line {line_number}")
            saw_preface = True
            continue
        match = _CHAPTER_RE.fullmatch(line)
        if match:
            number = chinese_number(match.group(1))
            if number != expected_number:
                if any(chapter["number"] == number for chapter in chapters):
                    reason = "duplicate chapter"
                else:
                    reason = "missing or out-of-order chapter"
                raise FixtureError(f"{reason} {number} at line {line_number}; expected {expected_number}")
            if current is not None:
                current["paragraphs"] = _flush_paragraphs(current["chapterId"], current.pop("_lines"))
                current["paragraphCount"] = len(current["paragraphs"])
                current["utf8ByteLength"] = _block_utf8_byte_length(current["paragraphs"])
                chapters.append(current)
            chapter_id = f"{EDITION_ID}-c{number:03d}"
            current = {
                "chapterId": chapter_id,
                "number": number,
                "title": match.group(2),
                "_lines": [],
            }
            expected_number += 1
            continue
        if line in (CHINESE_LICENSE_NOTICE, LICENSE_NOTICE):
            # The upstream fetch repeats these Wikisource public-domain notices after each page.
            # They are source-attributed metadata, not reader prose, and are intentionally excluded
            # from chapter paragraphs while remaining covered by sourceSha256 above.
            continue
        if current is None:
            if saw_preface:
                preface_lines.append(line)
            else:
                raise FixtureError(f"unexpected unassigned text at line {line_number}: {line!r}")
        else:
            current["_lines"].append(line)

    if current is not None:
        current["paragraphs"] = _flush_paragraphs(current["chapterId"], current.pop("_lines"))
        current["paragraphCount"] = len(current["paragraphs"])
        current["utf8ByteLength"] = _block_utf8_byte_length(current["paragraphs"])
        chapters.append(current)
    if len(chapters) != 120:
        raise FixtureError(f"expected exactly 120 chapters, got {len(chapters)}")
    if expected_number != 121:
        raise FixtureError(f"expected chapter sequence through 120, got next {expected_number}")
    if not all(chapter["paragraphs"] for chapter in chapters):
        raise FixtureError("empty chapter is not allowed")

    if not saw_preface:
        raise FixtureError("required 引首 heading is missing")

    preface = None
    if saw_preface:
        if not preface_lines:
            raise FixtureError("引首 is empty")
        preface_paragraphs = _flush_paragraphs(f"{EDITION_ID}-preface", preface_lines)
        preface = {
            "prefaceId": f"{EDITION_ID}-preface",
            "title": "引首",
            "paragraphs": preface_paragraphs,
            "paragraphCount": len(preface_paragraphs),
            "utf8ByteLength": _block_utf8_byte_length(preface_paragraphs),
        }

    preface_paragraph_count = preface["paragraphCount"] if preface else 0
    chapter_paragraph_count = sum(chapter["paragraphCount"] for chapter in chapters)
    preface_utf8_byte_length = preface["utf8ByteLength"] if preface else 0
    chapter_utf8_byte_length = sum(chapter["utf8ByteLength"] for chapter in chapters)
    reader_paragraph_count = preface_paragraph_count + chapter_paragraph_count
    manifest_without_hash = {
        "schemaVersion": 1,
        "workId": WORK_ID,
        "title": WORK_TITLE,
        "editionId": EDITION_ID,
        "source": {
            "file": "source/shuihu_raw.txt",
            "page": SOURCE_PAGE,
            "upstreamRepo": UPSTREAM_REPO,
            "upstreamCommit": UPSTREAM_COMMIT,
            "sha256": actual_sha256,
            "utf8ByteLength": len(raw),
            "excludedNoticeLines": [CHINESE_LICENSE_NOTICE, LICENSE_NOTICE],
        },
        "preface": preface,
        "prefaceParagraphCount": preface_paragraph_count,
        "chapterCount": len(chapters),
        "chapterParagraphCount": chapter_paragraph_count,
        "readerParagraphCount": reader_paragraph_count,
        "prefaceUtf8ByteLength": preface_utf8_byte_length,
        "chapterUtf8ByteLength": chapter_utf8_byte_length,
        "readerUtf8ByteLength": preface_utf8_byte_length + chapter_utf8_byte_length,
        "chapters": chapters,
    }
    manifest_sha256 = sha256_bytes(canonical_json_bytes(manifest_without_hash))
    manifest = dict(manifest_without_hash)
    manifest["manifestSha256"] = manifest_sha256
    return manifest


def write_outputs(source_path: Path, output_dir: Path) -> Tuple[Path, Path]:
    raw = source_path.read_bytes()
    manifest = parse_source(raw)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    summary_path = output_dir / "golden-summary.json"
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    chapters = manifest["chapters"]
    summary = {
        "editionId": manifest["editionId"],
        "workTitle": manifest["title"],
        "sourceSha256": manifest["source"]["sha256"],
        "manifestSha256": manifest["manifestSha256"],
        "chapterCount": manifest["chapterCount"],
        "prefaceParagraphCount": manifest["prefaceParagraphCount"],
        "chapterParagraphCount": manifest["chapterParagraphCount"],
        "readerParagraphCount": manifest["readerParagraphCount"],
        "prefaceUtf8ByteLength": manifest["prefaceUtf8ByteLength"],
        "chapterUtf8ByteLength": manifest["chapterUtf8ByteLength"],
        "readerUtf8ByteLength": manifest["readerUtf8ByteLength"],
        "representationSchemaVersion": REPRESENTATION_SCHEMA_VERSION,
        "catalogEtag": catalog_etag(manifest["manifestSha256"]),
        "prefaceEtag": block_etag(manifest["manifestSha256"], "PREFACE", manifest["preface"]),
        "firstChapterEtag": block_etag(manifest["manifestSha256"], "CHAPTER", chapters[0]),
        "lastChapterEtag": block_etag(manifest["manifestSha256"], "CHAPTER", chapters[-1]),
        "firstChapter": {"chapterId": chapters[0]["chapterId"], "title": chapters[0]["title"]},
        "lastChapter": {"chapterId": chapters[-1]["chapterId"], "title": chapters[-1]["title"]},
        "firstParagraphId": chapters[0]["paragraphs"][0]["paragraphId"],
        "lastParagraphId": chapters[-1]["paragraphs"][-1]["paragraphId"],
    }
    summary_path.write_bytes((json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
    return manifest_path, summary_path


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        manifest_path, summary_path = write_outputs(args.source, args.output_dir)
    except (OSError, FixtureError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {manifest_path}")
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
