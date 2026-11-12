import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "generate_manifest.py"
spec = importlib.util.spec_from_file_location("generate_manifest", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GenerateManifestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "source" / "shuihu_raw.txt").read_bytes()
        cls.manifest = module.parse_source(cls.source)

    def test_deterministic_repeat_output_and_summary_counts(self):
        first = self.manifest
        second = module.parse_source(self.source)
        self.assertEqual(module.canonical_json_bytes(first), module.canonical_json_bytes(second))
        self.assertEqual(first["source"]["sha256"], module.SOURCE_SHA256)
        self.assertEqual(first["title"], "水滸傳")
        self.assertEqual(first["chapterCount"], 120)
        self.assertEqual(first["prefaceParagraphCount"], 11)
        self.assertEqual(first["chapterParagraphCount"], 3666)
        self.assertEqual(first["readerParagraphCount"], 3677)
        self.assertNotIn("paragraphCount", first)
        self.assertEqual(first["chapters"][0]["chapterId"], "shuihuzhuan-zh-120-v1-c001")
        self.assertEqual(first["chapters"][-1]["chapterId"], "shuihuzhuan-zh-120-v1-c120")
        self.assertEqual(first["manifestSha256"], second["manifestSha256"])

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            module.write_outputs(ROOT / "source" / "shuihu_raw.txt", out)
            first_bytes = (out / "manifest.json").read_bytes()
            module.write_outputs(ROOT / "source" / "shuihu_raw.txt", out)
            self.assertEqual(first_bytes, (out / "manifest.json").read_bytes())
            self.assertEqual(
                hashlib.sha256(first_bytes).hexdigest(),
                hashlib.sha256((out / "manifest.json").read_bytes()).hexdigest(),
            )
            summary = json.loads((out / "golden-summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["prefaceParagraphCount"], 11)
            self.assertEqual(summary["chapterParagraphCount"], 3666)
            self.assertEqual(summary["readerParagraphCount"], 3677)
            self.assertEqual(summary["manifestSha256"], first["manifestSha256"])
            self.assertEqual((out / "manifest.json").read_bytes(), (ROOT / "manifest.json").read_bytes())
            self.assertEqual((out / "golden-summary.json").read_bytes(), (ROOT / "golden-summary.json").read_bytes())

    def test_exact_footer_exclusion_and_block_metrics(self):
        footer_count = self.source.count(module.LICENSE_NOTICE.encode("utf-8"))
        chinese_notice_count = self.source.count(module.CHINESE_LICENSE_NOTICE.encode("utf-8"))
        self.assertEqual(footer_count, 120)
        self.assertEqual(chinese_notice_count, 120)
        paragraphs = self.manifest["preface"]["paragraphs"][:]  # type: ignore
        for chapter in self.manifest["chapters"]:
            self.assertEqual(chapter["utf8ByteLength"], sum(p["utf8ByteLength"] for p in chapter["paragraphs"]))
            paragraphs.extend(chapter["paragraphs"])
        self.assertEqual(self.manifest["preface"]["utf8ByteLength"], sum(p["utf8ByteLength"] for p in self.manifest["preface"]["paragraphs"]))
        self.assertEqual(self.manifest["prefaceUtf8ByteLength"], self.manifest["preface"]["utf8ByteLength"])
        self.assertEqual(self.manifest["chapterUtf8ByteLength"], sum(c["utf8ByteLength"] for c in self.manifest["chapters"]))
        self.assertEqual(self.manifest["readerUtf8ByteLength"], self.manifest["prefaceUtf8ByteLength"] + self.manifest["chapterUtf8ByteLength"])
        self.assertEqual(len(paragraphs), 3677)
        reader_texts = [p["text"] for p in paragraphs]
        self.assertNotIn(module.LICENSE_NOTICE, reader_texts)
        self.assertNotIn(module.CHINESE_LICENSE_NOTICE, reader_texts)

    def test_exhaustive_ids_hashes_and_byte_lengths(self):
        preface = self.manifest["preface"]
        self.assertEqual(preface["prefaceId"], "shuihuzhuan-zh-120-v1-preface")
        for index, paragraph in enumerate(preface["paragraphs"], 1):
            self.assertEqual(paragraph["paragraphId"], "shuihuzhuan-zh-120-v1-preface-p%04d" % index)
            encoded = paragraph["text"].encode("utf-8")
            self.assertEqual(paragraph["utf8ByteLength"], len(encoded))
            self.assertEqual(paragraph["sha256"], hashlib.sha256(encoded).hexdigest())
        for chapter_number, chapter in enumerate(self.manifest["chapters"], 1):
            self.assertEqual(chapter["chapterId"], "shuihuzhuan-zh-120-v1-c%03d" % chapter_number)
            self.assertEqual(chapter["number"], chapter_number)
            for paragraph_number, paragraph in enumerate(chapter["paragraphs"], 1):
                expected_id = "%s-p%04d" % (chapter["chapterId"], paragraph_number)
                self.assertEqual(paragraph["paragraphId"], expected_id)
                encoded = paragraph["text"].encode("utf-8")
                self.assertEqual(paragraph["utf8ByteLength"], len(encoded))
                self.assertEqual(paragraph["sha256"], hashlib.sha256(encoded).hexdigest())


    def test_etag_golden_vectors_and_if_none_match_weak_comparison(self):
        manifest_sha = self.manifest["manifestSha256"]
        catalog = module.catalog_etag(manifest_sha)
        preface = module.block_etag(manifest_sha, "PREFACE", self.manifest["preface"])
        chapter_1 = module.block_etag(manifest_sha, "CHAPTER", self.manifest["chapters"][0])
        chapter_120 = module.block_etag(manifest_sha, "CHAPTER", self.manifest["chapters"][-1])
        self.assertEqual(catalog, 'W/"archive-catalog-json-v1-1656be0bc81b6d73a9bd2bf44121df36ae5a5a66f39f34114bf108e91e317ccc"')
        self.assertEqual(preface, 'W/"archive-block-json-v1-d42708515e0ea333504b54909892bda7650a1e13ef07099eed56c8b252fd5585"')
        self.assertEqual(chapter_1, 'W/"archive-block-json-v1-1ae662978ea0c7c1cd1d4c27b490b5c92d2a4560e04d595db6c2f4d7fadf1593"')
        self.assertEqual(chapter_120, 'W/"archive-block-json-v1-ee0c3091df1b93a99182b14819a26862cad7166f02855b40cebe079241b7736d"')
        self.assertTrue(module.if_none_match_matches(catalog, catalog))
        self.assertTrue(module.if_none_match_matches(catalog[2:], catalog))
        self.assertTrue(module.if_none_match_matches('"stale", ' + catalog, catalog))
        self.assertTrue(module.if_none_match_matches("*", catalog))
        self.assertFalse(module.if_none_match_matches('W/"stale"', catalog))
        with self.assertRaisesRegex(module.FixtureError, "malformed If-None-Match"):
            module.if_none_match_matches('W/"unterminated', catalog)
        with self.assertRaisesRegex(module.FixtureError, "malformed If-None-Match"):
            module.if_none_match_matches(catalog + ",", catalog)
        with self.assertRaisesRegex(module.FixtureError, "malformed If-None-Match"):
            module.if_none_match_matches('W/"stale tag"', catalog)
        with self.assertRaisesRegex(module.FixtureError, "malformed If-None-Match"):
            module.if_none_match_matches('W/"超"', catalog)
        self.assertFalse(module.if_none_match_matches('W/"stale,tag"', catalog))
        self.assertTrue(module.if_none_match_matches('\t' + catalog + ' \t', catalog))
        for malformed_ows in ('\v' + catalog, '\n' + catalog, '\r' + catalog, '\f' + catalog, '\u00a0' + catalog):
            with self.subTest(malformed_ows=repr(malformed_ows)):
                with self.assertRaisesRegex(module.FixtureError, "malformed If-None-Match"):
                    module.if_none_match_matches(malformed_ows, catalog)

    def test_utf8_byte_boundary_helper(self):
        text = "甲乙🙂"
        start = len("甲".encode("utf-8"))
        end = start + len("乙🙂".encode("utf-8"))
        self.assertEqual(module.utf8_byte_length(text), len(text.encode("utf-8")))
        self.assertEqual(module.validate_utf8_byte_range(text, start, end), "乙🙂")
        self.assertEqual(module.validate_utf8_byte_range(text, 0, 0), "")
        with self.assertRaisesRegex(module.FixtureError, "code-point boundaries"):
            module.validate_utf8_byte_range(text, start + 1, end)
        with self.assertRaisesRegex(module.FixtureError, "code-point boundaries"):
            module.validate_utf8_byte_range(text, 0, end - 1)
        with self.assertRaisesRegex(module.FixtureError, "out of bounds"):
            module.validate_utf8_byte_range(text, 0, len(text.encode("utf-8")) + 1)

    def test_rejects_bom_crlf_bare_cr_and_invalid_utf8(self):
        for label, altered in (
            ("BOM", b"\xef\xbb\xbf" + self.source),
            ("CRLF", self.source.replace(b"\n", b"\r\n")),
            ("bare CR", self.source.replace(b"\n", b"\r", 1)),
        ):
            with self.subTest(label=label):
                with self.assertRaises(module.FixtureError):
                    module.parse_source(altered, expected_sha256=None)
        with self.assertRaisesRegex(module.FixtureError, "valid UTF-8"):
            module.parse_source(b"\xff" + self.source, expected_sha256=None)
        with self.assertRaisesRegex(module.FixtureError, "terminal blank line"):
            module.parse_source(self.source + b"\n", expected_sha256=None)
        with self.assertRaisesRegex(module.FixtureError, "terminal blank line"):
            module.parse_source(self.source[:-1], expected_sha256=None)

    def test_rejects_empty_preface_chapter_and_paragraph(self):
        first_heading = self.source.index("第一回".encode("utf-8"))
        empty_preface = self.source[: self.source.index("引首".encode("utf-8")) + len("引首".encode("utf-8"))] + b"\n" + self.source[first_heading:]
        with self.assertRaisesRegex(module.FixtureError, "引首 is empty"):
            module.parse_source(empty_preface, expected_sha256=None)

        missing_preface = self.source[first_heading:]
        with self.assertRaisesRegex(module.FixtureError, "required 引首 heading is missing"):
            module.parse_source(missing_preface, expected_sha256=None)

        first_body = self.source.index(b"\n", first_heading) + 1
        second_heading = self.source.index("第二回".encode("utf-8"))
        empty_chapter = self.source[:first_body] + self.source[second_heading:]
        with self.assertRaisesRegex(module.FixtureError, "empty chapter"):
            module.parse_source(empty_chapter, expected_sha256=None)

        with self.assertRaisesRegex(module.FixtureError, "empty paragraph"):
            module._paragraph("empty", "")

    def test_rejects_malformed_chapter_sequence_and_source_hash_drift(self):
        original = self.source.decode("utf-8")
        malformed = original.replace("第二回 王教頭", "第一回 王教頭", 1).encode("utf-8")
        with self.assertRaisesRegex(module.FixtureError, "missing or out-of-order chapter|duplicate chapter"):
            module.parse_source(malformed, expected_sha256=None)
        altered = self.source.replace("引首".encode("utf-8"), "引首 ".encode("utf-8"), 1)
        with self.assertRaisesRegex(module.FixtureError, "source SHA-256 mismatch"):
            module.parse_source(altered)


if __name__ == "__main__":
    unittest.main()
