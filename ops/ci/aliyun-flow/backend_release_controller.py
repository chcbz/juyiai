#!/usr/bin/env python3
"""Read-only preparation for the backend Flow 5260799 release control plane.

This sidecar intentionally prepares immutable inputs only.  It neither updates a
Flow configuration nor starts a Flow run, and it never invokes a local build.
The optional ticket step delegates to the existing orchestrator-controlled
``flow-remote issue`` entry point exactly once.
"""

import argparse
import base64
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import zlib


ROOT = pathlib.Path(__file__).resolve().parents[3]
DEFAULT_API_REPO = ROOT / "api"
DEFAULT_TEMPLATE = (
    ROOT
    / "docs/implementation/plans/FLOW-CI-20260911-pipeline-5260799-r9-artifact-only-standard.yaml"
)
DEFAULT_ORCHESTRATOR = ROOT / "ops/orchestration/cyf_orchestrator.py"
PIPELINE_ID = "5260799"
ORGANIZATION_ID = "5fb7d76ee6f9d07f148529c7"
REPOSITORY_URL = "https://github.com/chcbz/juyiai-api.git"
BRANCH = "develop"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SAFE_TASK_ID = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
TICKET_B64 = re.compile(r"(TICKET_ZLIB_B64\s*=\s*)'[^']*'")
TICKET_SHA = re.compile(r"(TICKET_SHA256\s*=\s*)'[^']*'")
AUTO_APPROVE_INVOCATION = re.compile(
    r'((?:/usr/local/sbin/)?cyf-api-flow-auto-approve-install '
    r'"\$PIPELINE_ID" "\$BUILD_NUMBER" "\$CI_COMMIT_SHA")'
    r'(?: "[0-9a-f]{64}")?'
)


class ControllerError(RuntimeError):
    """An input is not safe enough to prepare a Flow candidate."""


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _require(value, label, pattern=None):
    if not isinstance(value, str) or not value or "\x00" in value or "\n" in value or "\r" in value:
        raise ControllerError("{} must be a non-empty single-line string".format(label))
    if pattern and not pattern.fullmatch(value):
        raise ControllerError("{} has an invalid format".format(label))
    return value


def _safe_repository_url(value):
    value = _require(value, "repository URL")
    if value != REPOSITORY_URL:
        raise ControllerError("repository URL must be the frozen credential-free backend origin")
    return value


def _git(repo, arguments, runner=subprocess.run):
    command = ["git", "-C", str(pathlib.Path(repo).resolve())] + list(arguments)
    completed = runner(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout or "git command failed").strip()[-500:]
        raise ControllerError("git validation failed: {}".format(detail))
    return completed.stdout.strip()


def read_remote_develop_sha(repository_url=REPOSITORY_URL, runner=subprocess.run):
    """Read the exact remote ``develop`` tip without changing local refs."""
    repository_url = _safe_repository_url(repository_url)
    completed = runner(
        ["git", "ls-remote", "--refs", repository_url, "refs/heads/{}".format(BRANCH)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if completed.returncode:
        raise ControllerError("remote develop lookup failed: {}".format((completed.stderr or "").strip()[-500:]))
    fields = completed.stdout.strip().split()
    if len(fields) != 2 or fields[1] != "refs/heads/{}".format(BRANCH) or not FULL_SHA.fullmatch(fields[0]):
        raise ControllerError("remote develop lookup returned no single full SHA")
    return fields[0]


def validate_local_api_source(api_git_repo, commit_sha, repository_url=REPOSITORY_URL, runner=subprocess.run):
    """Verify object existence, tree identity, origin provenance, and ancestry."""
    commit_sha = _require(commit_sha, "commit SHA", FULL_SHA)
    repository_url = _safe_repository_url(repository_url)
    repo = pathlib.Path(api_git_repo).resolve()
    if not repo.is_dir():
        raise ControllerError("API Git repository does not exist")
    _git(repo, ["cat-file", "-e", "{}^{{commit}}".format(commit_sha)], runner)
    tree_sha = _git(repo, ["rev-parse", "{}^{{tree}}".format(commit_sha)], runner)
    _require(tree_sha, "tree SHA", FULL_SHA)
    origin = _git(repo, ["remote", "get-url", "origin"], runner)
    if origin.rstrip("/") != repository_url.rstrip("/"):
        raise ControllerError("API origin does not match the frozen backend origin")
    _git(repo, ["show-ref", "--verify", "refs/remotes/origin/{}".format(BRANCH)], runner)
    ancestry = runner(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", commit_sha, "refs/remotes/origin/{}".format(BRANCH)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if ancestry.returncode:
        raise ControllerError("commit is not contained in origin/develop")
    return {"commit_sha": commit_sha, "tree_sha": tree_sha, "origin": origin, "branch": BRANCH}


def build_issue_command(*, task_id, ticket_path, api_git_repo, commit_sha, tree_sha,
                        selector, remote_cwd, remote_tool_root, remote_run_base,
                        ttl_seconds=3600, orchestrator=DEFAULT_ORCHESTRATOR):
    """Build the sole permitted ticket-issuance command; it performs no pipeline call."""
    task_id = _require(task_id, "task ID", SAFE_TASK_ID)
    commit_sha = _require(commit_sha, "commit SHA", FULL_SHA)
    tree_sha = _require(tree_sha, "tree SHA", FULL_SHA)
    selector = _require(selector, "selector", SAFE_TASK_ID)
    if not isinstance(ttl_seconds, int) or not 0 < ttl_seconds <= 6 * 60 * 60:
        raise ControllerError("ticket TTL must be between 1 and 21600 seconds")
    paths = {
        "ticket path": ticket_path,
        "API repository": api_git_repo,
        "remote cwd": remote_cwd,
        "remote tool root": remote_tool_root,
        "remote run base": remote_run_base,
        "orchestrator": orchestrator,
    }
    normalized = {}
    for label, value in paths.items():
        path = pathlib.Path(value).resolve()
        if not path.is_absolute() or ".." in path.parts:
            raise ControllerError("{} must be an absolute normalized path".format(label))
        normalized[label] = str(path)
    if not normalized["ticket path"].startswith("/tmp/cyf-flow-tickets/"):
        raise ControllerError("ticket path must be under /tmp/cyf-flow-tickets")
    return [
        sys.executable, normalized["orchestrator"], "flow-remote", "--", "issue",
        "--task-id", task_id, "--ticket", normalized["ticket path"],
        "--api-git-repo", normalized["API repository"], "--repo-url", REPOSITORY_URL,
        "--branch", BRANCH, "--commit-sha", commit_sha, "--tree-sha", tree_sha,
        "--selector", selector, "--flow-organization", ORGANIZATION_ID,
        "--flow-pipeline", PIPELINE_ID, "--remote-cwd", normalized["remote cwd"],
        "--remote-tool-root", normalized["remote tool root"],
        "--remote-run-base", normalized["remote run base"],
        "--ttl-seconds", str(ttl_seconds),
    ]


def issue_ticket_once(command, runner=subprocess.run):
    """Execute a prevalidated ticket command once, without retries or shell expansion."""
    if not isinstance(command, list) or len(command) < 5:
        raise ControllerError("refusing a non-flow-remote issue command")
    if pathlib.Path(command[1]).name != "cyf_orchestrator.py" or command[2:5] != ["flow-remote", "--", "issue"]:
        raise ControllerError("refusing a non-flow-remote issue command")
    allowed_flags = {
        "--task-id", "--ticket", "--api-git-repo", "--repo-url", "--branch",
        "--commit-sha", "--tree-sha", "--selector", "--flow-organization",
        "--flow-pipeline", "--remote-cwd", "--remote-tool-root", "--remote-run-base",
        "--ttl-seconds",
    }
    supplied_flags = command[5::2]
    if len(command[5:]) % 2 or set(supplied_flags) != allowed_flags or len(supplied_flags) != len(allowed_flags):
        raise ControllerError("refusing an unexpected ticket issue argument set")
    completed = runner(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if completed.returncode:
        raise ControllerError("ticket issue failed once: {}".format((completed.stderr or completed.stdout or "").strip()[-500:]))
    return completed.stdout


def render_ticket_only_template(template_bytes, ticket_bytes):
    """Replace exactly the historical ticket literals, preserving all other YAML bytes."""
    if not isinstance(template_bytes, bytes) or not isinstance(ticket_bytes, bytes):
        raise ControllerError("template and ticket must be bytes")
    text = template_bytes.decode("utf-8")
    if "PIPELINE = '{}'".format(PIPELINE_ID) not in text or "branch: develop" not in text:
        raise ControllerError("template is not the frozen 5260799 develop template")
    encoded = base64.b64encode(zlib.compress(ticket_bytes)).decode("ascii")
    ticket_sha = sha256_bytes(ticket_bytes)
    text, b64_count = TICKET_B64.subn(r"\1'{}'".format(encoded), text)
    text, sha_count = TICKET_SHA.subn(r"\1'{}'".format(ticket_sha), text)
    invocation_count = len(AUTO_APPROVE_INVOCATION.findall(text))
    has_vm_deploy = "VMDeploy" in text
    if invocation_count > 1 or has_vm_deploy and invocation_count != 1:
        raise ControllerError("deploy template must contain exactly one automatic deploy invocation")
    if invocation_count == 1:
        text = AUTO_APPROVE_INVOCATION.sub(r'\1 "{}"'.format(ticket_sha), text)
    if b64_count != 1 or sha_count != 1:
        raise ControllerError("template must contain exactly one ticket transport and SHA literal")
    rendered = text.encode("utf-8")
    return rendered, ticket_sha


def readback_summary(rendered_bytes, *, template_sha256, ticket_sha256):
    """Return only non-sensitive facts required for a future UpdatePipeline readback."""
    _require(template_sha256, "template SHA-256", SHA256)
    _require(ticket_sha256, "ticket SHA-256", SHA256)
    text = rendered_bytes.decode("utf-8")
    return {
        "pipeline_id": PIPELINE_ID,
        "candidate_config_sha256": sha256_bytes(rendered_bytes),
        "template_sha256": template_sha256,
        "ticket_sha256": ticket_sha256,
        "source_develop": "branch: develop" in text and "branchesFilter: develop" in text,
        "trigger_events_empty": "triggerEvents: []" in text,
        "java_build_count": len(re.findall(r"^\s*step: JavaBuild\s*$", text, re.MULTILINE)),
        "deploy_step_absent": "VMDeploy" not in text and "StartPipelineRun" not in text,
        "deploy_ticket_bound": (
            "VMDeploy" not in text
            or len(AUTO_APPROVE_INVOCATION.findall(text)) == 1
            and '{} "{}"'.format('"$CI_COMMIT_SHA"', ticket_sha256) in text
        ),
        "ticket_literals_present": len(TICKET_B64.findall(text)) == 1 and len(TICKET_SHA.findall(text)) == 1,
    }


def prepare_candidate(*, api_git_repo=DEFAULT_API_REPO, template=DEFAULT_TEMPLATE,
                      ticket_path, repository_url=REPOSITORY_URL, runner=subprocess.run):
    """Read remote provenance, validate local Git state, and render a ticket-only candidate."""
    remote_sha = read_remote_develop_sha(repository_url, runner)
    local = validate_local_api_source(api_git_repo, remote_sha, repository_url, runner)
    ticket_bytes = pathlib.Path(ticket_path).read_bytes()
    if not ticket_bytes:
        raise ControllerError("ticket file is empty")
    template_bytes = pathlib.Path(template).read_bytes()
    rendered, ticket_sha = render_ticket_only_template(template_bytes, ticket_bytes)
    return {
        "remote_develop_sha": remote_sha,
        "local_source": local,
        "readback": readback_summary(
            rendered, template_sha256=sha256_bytes(template_bytes), ticket_sha256=ticket_sha
        ),
        "rendered_yaml": rendered,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-git-repo", default=str(DEFAULT_API_REPO))
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    parser.add_argument("--ticket", required=True, help="existing immutable ticket; never printed")
    args = parser.parse_args(argv)
    candidate = prepare_candidate(api_git_repo=args.api_git_repo, template=args.template, ticket_path=args.ticket)
    output = dict(candidate["readback"])
    output["remote_develop_sha"] = candidate["remote_develop_sha"]
    output["local_tree_sha"] = candidate["local_source"]["tree_sha"]
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ControllerError as exc:
        print("BACKEND_RELEASE_CONTROLLER_DENIED: {}".format(exc), file=sys.stderr)
        raise SystemExit(2)
