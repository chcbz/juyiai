import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

from ops.performance.inventory import canonical_sha256, main, reconcile, scan_source, validate_registry, _runtime_routes


COMMIT = "c" * 40
TREE = "d" * 40
SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "inventory.py"))


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def artifact_sha256(value):
    return hashlib.sha256(json_bytes(value)).hexdigest()


def manifest(framework=None, management=None, profile="grey", commit=COMMIT, tree=TREE):
    if framework is None:
        framework = [{"method": "GET", "path": "/framework", "handler": "framework"}]
    if management is None:
        management = [{"method": "GET", "path": "/actuator/health", "handler": "health"}]
    return {
        "profile": profile,
        "api_commit": commit,
        "api_tree": tree,
        "framework_routes": framework,
        "management_routes": management,
        "error_routes": [{"method": "GET", "path": "/error", "handler": "error"}],
    }


def actuator(records):
    return {
        "contexts": {
            "application": {
                "mappings": {
                    "dispatcherServlets": {"dispatcherServlet": records},
                    "servletFilters": [],
                    "servlets": {},
                },
                "parentId": None,
            }
        }
    }


def runtime(framework_records, management_records, error_records=None, profile="grey", commit=COMMIT, tree=TREE):
    if error_records is None:
        error_records = [structured(["GET"], ["/error"], handler="error")]
    payload = {
        "framework_mappings": actuator(framework_records),
        "management_mappings": actuator(management_records),
        "error_mappings": actuator(error_records),
    }
    return {
        "profile": profile,
        "api_commit": commit,
        "api_tree": tree,
        "capture_content_sha256": canonical_sha256(payload),
        "payload": payload,
    }


def inventory_artifact(profile="grey", commit=COMMIT, tree=TREE):
    declared = manifest(profile=profile, commit=commit, tree=tree)
    source = "starter/src/main/java/example/OddEndpoint.java"
    return {
        "schema_version": 3,
        "profile": profile,
        "source": {
            "root": "/trusted/api",
            "api_commit": commit,
            "api_tree": tree,
            "dirty": False,
            "java_content_sha256": "a" * 64,
            "framework_manifest_content_sha256": canonical_sha256(declared),
        },
        "routes": [
            {
                "kind": "controller",
                "method": "GET",
                "path": "/x",
                "handler": source + ":x",
                "source": source,
                "line": 7,
            }
        ],
        "framework_manifest": declared,
        "diagnostics": [],
        "ok": True,
    }


def structured(methods, patterns, handler="Handler"):
    return {
        "handler": handler,
        "predicate": "ignored when Boot 4 structured details are present",
        "details": {
            "handlerMethod": {"className": "example.Handler", "name": "handle"},
            "requestMappingConditions": {
                "consumes": [],
                "headers": [],
                "methods": methods,
                "params": [],
                "patterns": patterns,
                "produces": [{"mediaType": "application/json", "negated": False}],
            },
        },
    }


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.roots = []

    def tearDown(self):
        for root in self.roots:
            shutil.rmtree(root, ignore_errors=True)

    def source(self, text, filename="DemoController.java"):
        root = tempfile.mkdtemp()
        self.roots.append(root)
        with open(os.path.join(root, filename), "w") as source_file:
            source_file.write(text)
        return root

    def reconcile_cli(
        self,
        inventory_value,
        runtime_value,
        inventory_sha256=None,
        runtime_sha256=None,
        expected_commit=COMMIT,
        expected_tree=TREE,
    ):
        root = tempfile.mkdtemp()
        self.roots.append(root)
        inventory_path = os.path.join(root, "inventory.json")
        runtime_path = os.path.join(root, "runtime.json")
        with open(inventory_path, "wb") as output_file:
            output_file.write(json_bytes(inventory_value))
        with open(runtime_path, "wb") as output_file:
            output_file.write(json_bytes(runtime_value))
        if inventory_sha256 is None:
            inventory_sha256 = artifact_sha256(inventory_value)
        if runtime_sha256 is None:
            runtime_sha256 = artifact_sha256(runtime_value)
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.Popen(
            [
                sys.executable,
                SCRIPT,
                "reconcile",
                "--inventory",
                inventory_path,
                "--runtime",
                runtime_path,
                "--profile",
                "grey",
                "--expected-api-commit",
                expected_commit,
                "--expected-api-tree",
                expected_tree,
                "--inventory-sha256",
                inventory_sha256,
                "--runtime-sha256",
                runtime_sha256,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        stdout, stderr = process.communicate()
        parsed = json.loads(stdout.decode("utf-8")) if stdout else None
        return process.returncode, parsed, stderr.decode("utf-8")

    def test_arrays_and_comments(self):
        root = self.source(
            '''@RestController\n@RequestMapping(path={"/a", "/b"})\nclass DemoController {\n'''
            ''' // @GetMapping("/fake")\n'''
            ''' @RequestMapping(value={"/x", "/y"}, method={RequestMethod.PUT, RequestMethod.DELETE})\n'''
            ''' public String run() { return "// literal"; }\n}'''
        )
        routes, diagnostics, _ = scan_source(root)
        self.assertEqual([], [item for item in diagnostics if item["fatal"]])
        self.assertEqual(8, len(routes))
        self.assertIn(("PUT", "/a/x"), {(item["method"], item["path"]) for item in routes})

    def test_missing_method_is_any(self):
        root = self.source(
            '@RequestMapping("/root")\nclass DemoController { @RequestMapping("/x") public void x() {} }'
        )
        routes, diagnostics, _ = scan_source(root)
        self.assertFalse(diagnostics)
        self.assertEqual("ANY", routes[0]["method"])

    def test_nonliteral_and_path_value_alias_collision_fail_closed(self):
        root = self.source(
            '@RequestMapping(path="/root", value="/alias")\nclass DemoController { '
            '@GetMapping(PATH) public void x() {} }'
        )
        routes, diagnostics, _ = scan_source(root)
        self.assertTrue(any(item["code"] == "unsupported_mapping" for item in diagnostics))
        self.assertEqual([], routes)

    def test_inheritance_fails_closed(self):
        root = self.source(
            '@RequestMapping("/root")\nclass DemoController extends BaseController { '
            '@GetMapping("/x") public void x() {} }'
        )
        _routes, diagnostics, _ = scan_source(root)
        self.assertTrue(any(item["code"] == "unsupported_inheritance" for item in diagnostics))

    def test_custom_mapping_annotations_are_never_silent(self):
        for annotation in ("MyGetMapping", "GM"):
            root = self.source(
                '@RestController\nclass DemoController { @%s("/x") public void x() {} }' % annotation,
                filename=annotation + "Controller.java",
            )
            routes, diagnostics, _ = scan_source(root)
            self.assertEqual([], routes)
            self.assertTrue(any(item["code"] == "unknown_declaration_annotation" for item in diagnostics))

    def test_dependency_defined_type_marker_is_diagnosed_before_filename_filter(self):
        root = self.source(
            '@GM\nclass OddEndpoint { public void x() {} }',
            filename="OddEndpoint.java",
        )
        routes, diagnostics, files = scan_source(root)
        self.assertEqual([], routes)
        self.assertTrue(any(item["code"] == "unknown_declaration_annotation" for item in diagnostics))
        self.assertTrue(any(path.endswith("OddEndpoint.java") for path in files))

    def test_composed_annotation_definition_outside_controller_filename_is_detected(self):
        root = self.source(
            '@GetMapping("/x")\n@Target(ElementType.METHOD)\npublic @interface MyGetMapping {}',
            filename="MyGetMapping.java",
        )
        routes, diagnostics, files = scan_source(root)
        self.assertEqual([], routes)
        self.assertTrue(any(item["code"] == "unsupported_composed_mapping" for item in diagnostics))
        self.assertTrue(any(path.endswith("MyGetMapping.java") for path in files))

    def test_rest_controller_outside_controller_filename_is_scanned(self):
        root = self.source(
            '@RestController\n@RequestMapping("/odd")\nclass OddEndpoint { @GetMapping("/x") public void x() {} }',
            filename="OddEndpoint.java",
        )
        routes, diagnostics, _ = scan_source(root)
        self.assertFalse(diagnostics)
        self.assertIn(("GET", "/odd/x"), {(item["method"], item["path"]) for item in routes})

    def test_known_nonmapping_allowlist_does_not_hide_mapping(self):
        root = self.source(
            '@Deprecated\n@RestController\n@RequestMapping("/root")\nclass DemoController { '
            '@Override\n@GetMapping("/x") public void x() {} }'
        )
        routes, diagnostics, _ = scan_source(root)
        self.assertFalse(any(item["code"] == "unknown_declaration_annotation" for item in diagnostics))
        self.assertEqual([("GET", "/root/x")], [(item["method"], item["path"]) for item in routes])

    def test_boot4_plural_methods_patterns_expand_cartesian_product(self):
        routes = _runtime_routes(actuator([structured(["GET", "POST"], ["/a", "/b"])]))
        self.assertEqual(
            {("GET", "/a"), ("GET", "/b"), ("POST", "/a"), ("POST", "/b")},
            {(item["method"], item["path"]) for item in routes},
        )

    def test_direct_method_and_path_arrays_expand_without_stringification(self):
        routes = _runtime_routes([{"methods": ["PUT", "DELETE"], "paths": ["/a", "/b"]}])
        self.assertEqual(4, len(routes))
        with self.assertRaisesRegex(Exception, "entries must be non-empty strings"):
            _runtime_routes([{"methods": ["GET"], "paths": [["/not-string"]]}])

    def test_malformed_runtime_records_are_rejected_not_skipped(self):
        bad_records = [
            [{"handler": "missing route"}],
            [{"method": "GET", "path": "/ok"}, "bad"],
            [{"methods": ["BREW"], "paths": ["/coffee"]}],
            [{"method": "GET", "path": "relative"}],
            [{"method": "GET", "path": "/x", "mystery": 1}],
        ]
        for records in bad_records:
            with self.assertRaises(Exception):
                _runtime_routes(records)

    def test_empty_or_unknown_actuator_surface_is_rejected(self):
        with self.assertRaisesRegex(Exception, "zero routes"):
            _runtime_routes(actuator([]))
        bad = actuator([{"predicate": "{GET [/x]}"}])
        bad["contexts"]["application"]["mappings"]["unknownSection"] = []
        with self.assertRaisesRegex(Exception, "unknown sections"):
            _runtime_routes(bad)

    def test_forged_or_missing_canonical_capture_hash_rejected(self):
        static = [{"method": "GET", "path": "/x", "handler": "x"}]
        fw = [structured(["GET"], ["/x"]), structured(["GET"], ["/framework"])]
        mgmt = [structured(["GET"], ["/actuator/health"])]
        for claimed in ("f" * 64, None, "not-a-hash"):
            capture = runtime(fw, mgmt)
            if claimed is None:
                capture.pop("capture_content_sha256")
            else:
                capture["capture_content_sha256"] = claimed
            result = reconcile(static, manifest(), capture, {"commit": COMMIT, "tree": TREE}, "grey")
            self.assertFalse(result["ok"])
            self.assertTrue(
                any(item["code"] in ("content_hash_missing", "content_hash_mismatch") for item in result["diagnostics"])
            )

    def test_canonical_payload_hash_is_format_independent_and_valid(self):
        static = [{"method": "GET", "path": "/x", "handler": "x"}]
        capture = runtime(
            [structured(["GET"], ["/x"]), structured(["GET"], ["/framework"])],
            [structured(["GET"], ["/actuator/health"])],
        )
        reparsed = json.loads(json.dumps(capture, indent=4, sort_keys=False))
        result = reconcile(static, manifest(), reparsed, {"commit": COMMIT, "tree": TREE}, "grey")
        self.assertTrue(result["ok"], result["diagnostics"])

    def test_manifest_requires_exact_binding_and_nonempty_distinct_lists(self):
        static = [{"method": "GET", "path": "/x", "handler": "x"}]
        capture = runtime(
            [structured(["GET"], ["/x"]), structured(["GET"], ["/framework"])],
            [structured(["GET"], ["/actuator/health"])],
        )
        invalid = [
            {"profile": "grey", "routes": []},
            manifest(framework=[], management=[]),
            manifest(commit="wrong"),
            manifest(framework=[{"method": "GET", "path": [["/bad"]]}]),
            dict(manifest(), mystery=[]),
        ]
        for declared in invalid:
            result = reconcile(static, declared, capture, {"commit": COMMIT, "tree": TREE}, "grey")
            self.assertFalse(result["ok"])
            self.assertTrue(any(item["code"] in ("binding_missing", "binding_mismatch", "manifest_shape") for item in result["diagnostics"]))

    def test_runtime_binding_and_nonempty_distinct_surfaces_required(self):
        static = [{"method": "GET", "path": "/x", "handler": "x"}]
        good_fw = [structured(["GET"], ["/x"]), structured(["GET"], ["/framework"])]
        good_mgmt = [structured(["GET"], ["/actuator/health"])]
        captures = [
            runtime(good_fw, good_mgmt, profile="prod"),
            runtime(good_fw, good_mgmt, tree="wrong"),
            runtime([], good_mgmt),
            runtime(good_fw, []),
        ]
        for capture in captures:
            result = reconcile(static, manifest(), capture, {"commit": COMMIT, "tree": TREE}, "grey")
            self.assertFalse(result["ok"])

    def test_framework_and_management_surfaces_cannot_cross_cancel(self):
        static = [{"method": "GET", "path": "/x", "handler": "x"}]
        capture = runtime(
            [
                structured(["GET"], ["/x"]),
                structured(["GET"], ["/framework-other"]),
                structured(["GET"], ["/actuator/health"]),
            ],
            [structured(["GET"], ["/management-other"])],
        )
        result = reconcile(static, manifest(), capture, {"commit": COMMIT, "tree": TREE}, "grey")
        self.assertFalse(result["ok"])
        messages = "\n".join(item["message"] for item in result["diagnostics"])
        self.assertIn("management declared route missing", messages)
        self.assertIn("framework runtime route not declared", messages)

    def test_scan_cli_rejects_unbound_empty_framework_manifest(self):
        root = self.source(
            '@RestController\n@RequestMapping("/root")\nclass DemoController { '
            '@GetMapping("/x") public void x() {} }'
        )
        subprocess.check_call(["git", "init", "-q", root])
        subprocess.check_call(["git", "-C", root, "add", "DemoController.java"])
        subprocess.check_call(
            ["git", "-C", root, "-c", "user.name=Inventory Test", "-c", "user.email=inventory@example.invalid", "commit", "-qm", "fixture"]
        )
        commit = subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"]).decode().strip()
        tree = subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD^{tree}"]).decode().strip()
        fixture_dir = tempfile.mkdtemp()
        self.roots.append(fixture_dir)
        manifest_path = os.path.join(fixture_dir, "manifest.json")
        output_path = os.path.join(fixture_dir, "inventory.json")
        registry_path = os.path.join(fixture_dir, "registry.json")
        with open(manifest_path, "w") as output_file:
            json.dump({"profile": "grey", "routes": []}, output_file)
        with open(registry_path, "w") as output_file:
            json.dump({"routes": [{"kind": "controller", "method": "GET", "path": "/root/x"}]}, output_file)
        rc = main(
            [
                "scan",
                "--source-root",
                root,
                "--profile",
                "grey",
                "--api-commit",
                commit,
                "--api-tree",
                tree,
                "--framework-manifest",
                manifest_path,
                "--registry-json",
                registry_path,
                "--output",
                output_path,
            ]
        )
        self.assertEqual(2, rc)
        with open(output_path) as input_file:
            result = json.load(input_file)
        self.assertFalse(result["ok"])
        self.assertTrue(any(item["code"] in ("binding_missing", "manifest_shape") for item in result["diagnostics"]))

    def test_real_reconcile_cli_accepts_independently_pinned_valid_fixture(self):
        inventory_value = inventory_artifact()
        runtime_value = runtime(
            [structured(["GET"], ["/x"]), structured(["GET"], ["/framework"])],
            [structured(["GET"], ["/actuator/health"])],
        )
        trusted_inventory_hash = artifact_sha256(inventory_value)
        trusted_runtime_hash = artifact_sha256(runtime_value)
        rc, result, stderr = self.reconcile_cli(
            inventory_value,
            runtime_value,
            inventory_sha256=trusted_inventory_hash,
            runtime_sha256=trusted_runtime_hash,
        )
        self.assertEqual("", stderr)
        self.assertEqual(0, rc, result)
        self.assertTrue(result["ok"], result["diagnostics"])

    def test_real_reconcile_cli_original_pin_binds_routes_diagnostics_and_source_digest(self):
        original = inventory_artifact()
        trusted_hash = artifact_sha256(original)
        runtime_value = runtime(
            [structured(["GET"], ["/x"]), structured(["GET"], ["/framework"])],
            [structured(["GET"], ["/actuator/health"])],
        )
        mutations = []
        routes = json.loads(json.dumps(original))
        routes["routes"][0]["path"] = "/tampered"
        mutations.append(("routes", routes))
        diagnostics = json.loads(json.dumps(original))
        diagnostics["diagnostics"] = [
            {"code": "class_path_array", "message": "tampered diagnostic", "fatal": False}
        ]
        mutations.append(("diagnostics", diagnostics))
        source_digest = json.loads(json.dumps(original))
        source_digest["source"]["java_content_sha256"] = "b" * 64
        mutations.append(("source digest", source_digest))

        for label, tampered in mutations:
            rc, result, _stderr = self.reconcile_cli(
                tampered, runtime_value, inventory_sha256=trusted_hash
            )
            self.assertEqual(2, rc, label)
            self.assertTrue(
                any(item["code"] == "inventory_file_hash_mismatch" for item in result["diagnostics"]),
                (label, result),
            )

    def test_real_reconcile_cli_rejects_strict_inventory_mutations(self):
        runtime_value = runtime(
            [structured(["GET"], ["/x"]), structured(["GET"], ["/framework"])],
            [structured(["GET"], ["/actuator/health"])],
        )
        cases = []

        pins = inventory_artifact()
        pins["source"]["api_commit"] = "e" * 40
        pins["framework_manifest"]["api_commit"] = "e" * 40
        pins["source"]["framework_manifest_content_sha256"] = canonical_sha256(pins["framework_manifest"])
        cases.append(("pins", pins, "binding_mismatch"))

        schema = inventory_artifact()
        schema["schema_version"] = 99
        cases.append(("schema", schema, "inventory_schema"))

        diagnostics = inventory_artifact()
        diagnostics["diagnostics"] = [{"code": "forged_diagnostic", "message": "forged", "fatal": False}]
        cases.append(("diagnostics", diagnostics, "inventory_diagnostics_shape"))

        dirty = inventory_artifact()
        dirty["source"]["dirty"] = True
        cases.append(("dirty", dirty, "source_dirty"))

        source_digest = inventory_artifact()
        source_digest["source"]["java_content_sha256"] = "not-a-sha256"
        cases.append(("source digest", source_digest, "inventory_source_shape"))

        content = inventory_artifact()
        content["framework_manifest"]["framework_routes"][0]["path"] = "/changed"
        cases.append(("content", content, "inventory_content_mismatch"))

        for label, inventory_value, code in cases:
            rc, result, _stderr = self.reconcile_cli(inventory_value, runtime_value)
            self.assertEqual(2, rc, label)
            self.assertTrue(any(item["code"] == code for item in result["diagnostics"]), (label, result))

    def test_real_reconcile_cli_rejects_capture_binding_tamper(self):
        inventory_value = inventory_artifact()
        runtime_value = runtime(
            [structured(["GET"], ["/x"]), structured(["GET"], ["/framework"])],
            [structured(["GET"], ["/actuator/health"])],
            tree="e" * 40,
        )
        rc, result, _stderr = self.reconcile_cli(inventory_value, runtime_value)
        self.assertEqual(2, rc)
        self.assertTrue(any(item["code"] == "binding_mismatch" for item in result["diagnostics"]))

    def test_real_reconcile_cli_rejects_coherently_forged_pair_against_original_artifact_pins(self):
        original_inventory = inventory_artifact()
        original_runtime = runtime(
            [structured(["GET"], ["/x"]), structured(["GET"], ["/framework"])],
            [structured(["GET"], ["/actuator/health"])],
        )
        trusted_inventory_hash = artifact_sha256(original_inventory)
        trusted_runtime_hash = artifact_sha256(original_runtime)

        forged_inventory = json.loads(json.dumps(original_inventory))
        forged_inventory["routes"][0]["path"] = "/forged"
        forged_runtime = runtime(
            [structured(["GET"], ["/forged"]), structured(["GET"], ["/framework"])],
            [structured(["GET"], ["/actuator/health"])],
        )
        rc, result, _stderr = self.reconcile_cli(
            forged_inventory,
            forged_runtime,
            inventory_sha256=trusted_inventory_hash,
            runtime_sha256=trusted_runtime_hash,
        )
        self.assertEqual(2, rc)
        codes = set(item["code"] for item in result["diagnostics"])
        self.assertIn("inventory_file_hash_mismatch", codes)
        self.assertIn("runtime_file_hash_mismatch", codes)

    def test_reconcile_snapshots_each_artifact_once_before_path_swap(self):
        root = tempfile.mkdtemp()
        self.roots.append(root)
        inventory_path = os.path.join(root, "inventory.json")
        runtime_path = os.path.join(root, "runtime.json")
        original_inventory = inventory_artifact()
        original_runtime = runtime(
            [structured(["GET"], ["/x"]), structured(["GET"], ["/framework"])],
            [structured(["GET"], ["/actuator/health"])],
        )
        forged_inventory = json.loads(json.dumps(original_inventory))
        forged_inventory["routes"][0]["path"] = "/forged"
        forged_runtime = runtime(
            [structured(["GET"], ["/forged"]), structured(["GET"], ["/framework"])],
            [structured(["GET"], ["/actuator/health"])],
        )
        with open(inventory_path, "wb") as output_file:
            output_file.write(json_bytes(original_inventory))
        with open(runtime_path, "wb") as output_file:
            output_file.write(json_bytes(original_runtime))

        replacements = {
            inventory_path: json_bytes(forged_inventory),
            runtime_path: json_bytes(forged_runtime),
        }
        open_counts = {inventory_path: 0, runtime_path: 0}
        real_open = open

        def swap_after_open(path, *args, **kwargs):
            handle = real_open(path, *args, **kwargs)
            normalized = os.path.abspath(path)
            if normalized in replacements:
                open_counts[normalized] += 1
                if open_counts[normalized] == 1:
                    replacement_path = normalized + ".replacement"
                    with real_open(replacement_path, "wb") as replacement_file:
                        replacement_file.write(replacements[normalized])
                    os.replace(replacement_path, normalized)
            return handle

        stdout = io.StringIO()
        with mock.patch("builtins.open", side_effect=swap_after_open), redirect_stdout(stdout):
            rc = main(
                [
                    "reconcile",
                    "--inventory",
                    inventory_path,
                    "--runtime",
                    runtime_path,
                    "--profile",
                    "grey",
                    "--expected-api-commit",
                    COMMIT,
                    "--expected-api-tree",
                    TREE,
                    "--inventory-sha256",
                    artifact_sha256(original_inventory),
                    "--runtime-sha256",
                    artifact_sha256(original_runtime),
                ]
            )

        result = json.loads(stdout.getvalue())
        self.assertEqual(0, rc, result)
        self.assertEqual({inventory_path: 1, runtime_path: 1}, open_counts)
        self.assertEqual(["/x"], [route["path"] for route in result["static"]])
        self.assertNotIn("/forged", json.dumps(result, sort_keys=True))


    def test_error_surface_is_required_and_reconciled_independently(self):
        static = [{"method": "GET", "path": "/x", "handler": "x"}]
        good = runtime(
            [structured(["GET"], ["/x"]), structured(["GET"], ["/framework"])],
            [structured(["GET"], ["/actuator/health"])],
            [structured(["GET"], ["/error"], handler="error")],
        )
        result = reconcile(static, manifest(), good, {"commit": COMMIT, "tree": TREE}, "grey")
        self.assertTrue(result["ok"], result["diagnostics"])
        moved = runtime(
            [structured(["GET"], ["/x"]), structured(["GET"], ["/framework"]),
             structured(["GET"], ["/error"])],
            [structured(["GET"], ["/actuator/health"])],
            [structured(["GET"], ["/other-error"], handler="error")],
        )
        result = reconcile(static, manifest(), moved, {"commit": COMMIT, "tree": TREE}, "grey")
        self.assertFalse(result["ok"])
        messages = "\n".join(item["message"] for item in result["diagnostics"])
        self.assertIn("error declared route missing", messages)
        self.assertIn("error runtime route not declared", messages)

    def test_registry_is_an_exact_four_surface_projection(self):
        surfaces = (
            ("controller", [{"method": "GET", "path": "/x"}]),
            ("framework", [{"method": "GET", "path": "/framework"}]),
            ("management", [{"method": "GET", "path": "/actuator/health"}]),
            ("error", [{"method": "GET", "path": "/error"}]),
        )
        good = {"routes": [
            {"kind": kind, "method": route["method"], "path": route["path"]}
            for kind, routes in surfaces for route in routes
        ]}
        self.assertEqual([], validate_registry(good, surfaces))
        missing = {"routes": good["routes"][:-1]}
        self.assertTrue(any(item["code"] == "registry_missing" for item in validate_registry(missing, surfaces)))
        unknown = {"routes": good["routes"] + [{"kind": "framework", "method": "GET", "path": "/dynamic/{*path}"}]}
        codes = {item["code"] for item in validate_registry(unknown, surfaces)}
        self.assertIn("registry_wildcard", codes)
        self.assertIn("registry_unknown", codes)
        malformed = {"routes": [{"kind": "framework", "method": "GET", "path": "/framework", "extra": 1}]}
        self.assertTrue(any(item["code"] == "registry_shape" for item in validate_registry(malformed, surfaces)))

    def test_json_media_is_not_stream_exemption(self):
        root = self.source(
            '@RequestMapping("/media/upload")\nclass DemoController { '
            '@PostMapping("/x") public void x() {} }'
        )
        routes, diagnostics, _ = scan_source(root)
        self.assertFalse(diagnostics)
        self.assertIn(("POST", "/media/upload/x"), {(item["method"], item["path"]) for item in routes})


if __name__ == "__main__":
    unittest.main()
