"""Real Git hooks must reject invalid messages and unverified outgoing snapshots."""
import json
import os
from unittest.mock import patch
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parent.parent
TITLE = "docs: update fixture guide"
BODY = "\n\nChanges:\n- Update guide.\n\nAffected Files:\n- README.md\n\nVerification:\n- Fixture.\n"


class GitHookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "work"
        self.root.mkdir()
        self.command("git", "init", "-q", "-b", "main")
        self.command("git", "config", "user.email", "test@example.com")
        self.command("git", "config", "user.name", "Fixture")
        for name in ("git_hooks.py", "validate_git_governance.py"):
            target = self.root / "scripts" / name
            target.parent.mkdir(exist_ok=True)
            shutil.copy2(SOURCE / "scripts" / name, target)
        shutil.copytree(SOURCE / ".githooks", self.root / ".githooks")
        (self.root / "Makefile").write_text("verify-plan:\n\t@echo Plan\nverify:\n\t@echo verified >> .git/fixture-verification\n")
        (self.root / "README.md").write_text("Initial\n")
        self.command("git", "add", ".")
        self.command("git", "commit", "-qm", "fixture seed")
        self.remote = Path(self.temp.name) / "remote.git"
        self.command("git", "init", "--bare", "-q", str(self.remote))
        self.command("git", "remote", "add", "origin", str(self.remote))
        self.command("git", "push", "-q", "origin", "main")
        self.command("git", "switch", "-qc", "docs/fixture-guide")
        self.command("python3", "scripts/git_hooks.py", "install")

    def command(self, *args, ok=True):
        result = subprocess.run(args, cwd=self.root, text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def prepare(self, stage_log=True):
        (self.root / "README.md").write_text("Updated guide\n")
        log = self.root / "worklog/0001-fixture-guide.md"
        log.parent.mkdir(exist_ok=True)
        sections = ["Commit Title", "Changed File Scope", "Reason", "Design", "Verification Plan", "Impact", "Loop Alignment", "Verification"]
        log.write_text("\n".join(f"# {s}\n\n{TITLE if s == 'Commit Title' else 'Fixture evidence.'}\n" for s in sections))
        self.command("git", "add", "README.md")
        if stage_log:
            self.command("git", "add", "worklog")

    def commit(self):
        self.prepare()
        self.command("git", "commit", "-qm", TITLE + BODY)

    def test_commit_message_and_staged_worklog_are_required(self):
        self.prepare(stage_log=False)
        self.assertIn("worklog", self.command("git", "commit", "-qm", TITLE + BODY, ok=False))
        self.command("git", "add", "worklog")
        self.assertIn("invalid Conventional", self.command("git", "commit", "-qm", "invalid" + BODY, ok=False))
        self.command("git", "commit", "-qm", TITLE + BODY)

    def test_korean_commit_and_pr_titles(self):
        self.prepare()
        title = "docs: 한국어 개발 문서를 갱신한다"
        log = self.root / "worklog/0001-fixture-guide.md"
        log.write_text(log.read_text().replace(TITLE, title))
        self.command("git", "add", "worklog")
        self.command("git", "commit", "-qm", title + BODY)
        body = self.root / ".git/pr.md"
        body.write_text("\n".join(f"## {h}\n\n검증한 변경 내용.\n" for h in ("Summary", "Scope", "Reason", "Verification", "Documentation", "Risk / Impact")))
        self.command("python3", "scripts/validate_git_governance.py", "--pr-title", "[docs] 한국어 개발 문서 갱신", "--pr-body-file", str(body))

    def test_push_runs_local_plan_and_verification(self):
        self.commit()
        self.command("git", "push", "-q", "origin", "HEAD")
        self.assertEqual((self.root / ".git/fixture-verification").read_text(), "verified\n")

    def test_dirty_worktree_and_different_head_are_rejected(self):
        self.commit()
        (self.root / "README.md").write_text("Uncommitted\n")
        self.assertIn("Commit or stash", self.command("git", "push", "origin", "HEAD", ok=False))
        self.command("git", "restore", "README.md")
        self.command("git", "branch", "docs/old", "main")
        self.assertIn("checked-out HEAD", self.command("git", "push", "origin", "docs/old", ok=False))

    def test_failed_verification_blocks_push(self):
        self.prepare()
        (self.root / "Makefile").write_text("verify-plan:\n\t@echo Plan\nverify:\n\t@exit 1\n")
        self.command("git", "add", "Makefile")
        self.command("git", "commit", "-qm", TITLE + BODY)
        self.assertIn("Local Git check failed", self.command("git", "push", "origin", "HEAD", ok=False))
        self.assertEqual(self.command("git", "ls-remote", "--heads", "origin", "docs/fixture-guide"), "")

    def test_push_rechecks_authored_commits_even_if_commit_hook_was_bypassed(self):
        self.prepare()
        self.command("git", "-c", "core.hooksPath=/dev/null", "commit", "-qm", "bad commit")
        self.assertIn("invalid Conventional", self.command("git", "push", "origin", "HEAD", ok=False))

    def test_main_and_invalid_branch_pushes_are_rejected(self):
        self.commit()
        self.assertIn("pull request", self.command("git", "push", "origin", "HEAD:main", ok=False))
        self.assertIn("destination branch", self.command("git", "push", "origin", "HEAD:wrong_name", ok=False))

    def main_rebase_approval(self):
        previous = self.command("git", "rev-parse", "main").strip()
        head = self.command("git", "rev-parse", "HEAD").strip()
        backup = "refs/heads/chore/main-before-rebase"
        self.command("git", "update-ref", "refs/remotes/upstream/main", previous)
        self.command("git", "--git-dir", str(self.remote), "update-ref", backup, previous)
        folder = self.root / ".git/approvals"
        folder.mkdir(exist_ok=True)
        path = folder / "main-rebase.json"
        data = dict(remote="origin", expected_main=previous, new_head=head,
                    upstream_main=previous, backup_ref=backup)
        path.write_text(json.dumps(data))
        return path, data

    def test_exact_main_rebase_approval_still_runs_verification(self):
        self.commit()
        path, data = self.main_rebase_approval()
        with patch.dict(os.environ, CANVANITY_MAIN_REBASE_APPROVAL=str(path)):
            self.command("git", "push", "--force-with-lease=refs/heads/main:" + data["expected_main"], "origin", "HEAD:main")
        self.assertEqual((self.root / ".git/fixture-verification").read_text(), "verified\n")
        self.assertTrue(self.command("git", "ls-remote", "origin", "main").startswith(data["new_head"]))

    def test_main_rebase_rejects_mismatched_head_previous_and_upstream(self):
        self.commit()
        path, data = self.main_rebase_approval()
        for field in ("expected_main", "new_head", "upstream_main"):
            with self.subTest(field=field), patch.dict(os.environ, CANVANITY_MAIN_REBASE_APPROVAL=str(path)):
                path.write_text(json.dumps({**data, field: "0" * 40}))
                self.command("git", "push", "origin", "HEAD:main", ok=False)
                self.assertTrue(self.command("git", "ls-remote", "origin", "main").startswith(data["expected_main"]))

    def test_main_rebase_requires_remote_backup(self):
        self.commit()
        path, data = self.main_rebase_approval()
        self.command("git", "--git-dir", str(self.remote), "update-ref", "-d", data["backup_ref"])
        with patch.dict(os.environ, CANVANITY_MAIN_REBASE_APPROVAL=str(path)):
            self.assertIn("exact remote backup", self.command("git", "push", "origin", "HEAD:main", ok=False))

    def test_main_rebase_approval_never_skips_failed_verification(self):
        self.prepare()
        (self.root / "Makefile").write_text("verify-plan:\n\t@echo Plan\nverify:\n\t@exit 1\n")
        self.command("git", "add", "Makefile")
        self.command("git", "commit", "-qm", TITLE + BODY)
        path, data = self.main_rebase_approval()
        with patch.dict(os.environ, CANVANITY_MAIN_REBASE_APPROVAL=str(path)):
            self.assertIn("Local Git check failed", self.command("git", "push", "origin", "HEAD:main", ok=False))
        self.assertTrue(self.command("git", "ls-remote", "origin", "main").startswith(data["expected_main"]))

    def test_install_refuses_to_replace_custom_hooks(self):
        self.command("git", "config", "core.hooksPath", "custom-hooks")
        self.assertIn("Existing core.hooksPath", self.command("python3", "scripts/git_hooks.py", "install", ok=False))
        self.assertEqual(self.command("git", "config", "--get", "core.hooksPath").strip(), "custom-hooks")

    def test_workflows_are_manual_only_and_rules_keep_pr_protection(self):
        for workflow in (SOURCE / ".github/workflows").glob("*.yml"):
            events = workflow.read_text().split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
            self.assertIn("    workflow_dispatch:", events)
            for event in ("pull_request:", "push:", "schedule:", "release:"):
                self.assertNotIn("\n    " + event, events)
        rules = json.loads((SOURCE / ".github/main-ruleset.json").read_text())["rules"]
        types = {rule["type"] for rule in rules}
        self.assertEqual(types, {"pull_request", "deletion", "non_fast_forward"})
        pr = next(rule for rule in rules if rule["type"] == "pull_request")
        self.assertTrue(pr["parameters"]["required_review_thread_resolution"])
