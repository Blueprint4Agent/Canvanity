"""Versioned commit/push checks and local PR metadata validation."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
import validate_git_governance as governance


def run(*args, **kwargs):
    return subprocess.check_output(args, text=True, **kwargs).strip()


def git(*args):
    return run("git", *args)


def require(value, message):
    if not value:
        raise ValueError(message)


def install():
    current = subprocess.run(["git", "config", "--get", "core.hooksPath"], capture_output=True, text=True)
    require(not current.stdout.strip() or current.stdout.strip() == ".githooks",
            "Existing core.hooksPath is configured; reconcile it before installing these hooks.")
    for name in ("commit-msg", "pre-push"):
        require(os.access(Path(".githooks") / name, os.X_OK), f"Missing executable hook: {name}")
    subprocess.run(["git", "config", "--local", "core.hooksPath", ".githooks"], check=True)
    print("Installed commit-msg and pre-push hooks for this clone.")


def commit_message(path):
    # Integration merges have no authored per-commit worklog requirement.
    if subprocess.run(["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"], stdout=subprocess.DEVNULL).returncode == 0:
        print("Integration merge: per-commit worklog check not applicable.")
        return
    message = subprocess.check_output(["git", "stripspace", "--strip-comments"], input=Path(path).read_text(), text=True)
    require(message.strip(), "Commit message is empty")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt") as file:
        file.write(message)
        file.flush()
        subprocess.run([sys.executable, "scripts/validate_git_governance.py", "--commit-title", message.splitlines()[0], "--commit-body-file", file.name], check=True)


def clean_environment():
    env = os.environ.copy()
    # Git exports repository-local variables to hooks; do not leak these into child Git commands.
    for key in git("rev-parse", "--local-env-vars").splitlines():
        env.pop(key, None)
    for key in ("VERIFY_BASE", "VERIFY_HEAD", "VERIFY_FULL", "COMMIT_TITLE", "COMMIT_BODY_FILE", "PR_TITLE", "PR_BODY_FILE", "CANVANITY_MAIN_REBASE_APPROVAL"):
        env.pop(key, None)
    return env


def authorize_main_rebase(remote, head, previous):
    """An explicit, exact-ref authorization never skips ordinary push checks."""
    filename = os.environ.get("CANVANITY_MAIN_REBASE_APPROVAL")
    require(filename, "Use a pull request to update main; an explicitly approved rebase requires an exact-ref authorization")
    path = Path(filename).resolve()
    approvals = Path(git("rev-parse", "--absolute-git-dir")).resolve() / "approvals"
    require(path.parent == approvals, "Main rebase approval must be inside the local Git approvals directory")
    approval = json.loads(path.read_text())
    require(remote == "origin" and approval.get("remote") == remote, "Main rebase approval is restricted to origin")
    require(approval.get("expected_main") == previous and approval.get("new_head") == head,
            "Main rebase approval does not match the old/new SHA pair")
    upstream = git("rev-parse", "refs/remotes/upstream/main")
    require(approval.get("upstream_main") == upstream, "Main rebase approval has a different upstream base")
    require(subprocess.run(["git", "merge-base", "--is-ancestor", upstream, head],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0,
            "The approved upstream base must be an ancestor of the new main")
    backup = approval.get("backup_ref", "")
    require(backup.startswith("refs/heads/chore/") and governance.BRANCH.fullmatch(backup.removeprefix("refs/heads/")),
            "Main rebase requires a valid chore backup ref")
    require(git("ls-remote", "--heads", remote, backup) == f"{previous}\t{backup}",
            "Main rebase requires an exact remote backup of the previous main")
    print("Exact-ref main rebase authorization validated; ordinary push checks still apply.")


def pre_push(remote, lines):
    updates = []
    for line in lines.splitlines():
        fields = line.split()
        require(len(fields) == 4, "Malformed pre-push ref update")
        local_ref, sha, remote_ref, previous = fields
        if set(sha) == {"0"}:
            require(remote_ref != "refs/heads/main", "Deleting main is prohibited")
            continue
        if remote_ref == "refs/heads/main":
            authorize_main_rebase(remote, sha, previous)
        elif remote_ref.startswith("refs/heads/"):
            require(governance.BRANCH.fullmatch(remote_ref.removeprefix("refs/heads/")), "Invalid destination branch name")
        require(remote_ref.startswith(("refs/heads/", "refs/tags/")), "Unsupported push ref")
        head = git("rev-parse", f"{sha}^{{commit}}")
        require(head == git("rev-parse", "HEAD"), "Push only the checked-out HEAD; switch to the branch/ref first")
        if local_ref.startswith("refs/heads/"):
            require(governance.BRANCH.fullmatch(local_ref.removeprefix("refs/heads/")), "Invalid source branch name")
        updates.append(head)
    if not updates:
        return
    require(not git("status", "--porcelain", "--untracked-files=normal"), "Commit or stash working-tree/submodule changes before pushing; verification must match pushed HEAD")
    env = clean_environment()
    subprocess.run(["git", "fetch", "--no-tags", remote, "refs/heads/main"], check=True, env=env)
    base = git("merge-base", "FETCH_HEAD", "HEAD")
    for sha in git("rev-list", "--reverse", "--no-merges", f"{base}..HEAD").splitlines():
        governance.check_commit(sha)
    env.update(VERIFY_BASE=base, VERIFY_HEAD=git("rev-parse", "HEAD"))
    subprocess.run(["make", "verify-plan"], check=True, env=env)
    subprocess.run(["make", "verify"], check=True, env=env)
    require(not git("status", "--porcelain", "--untracked-files=normal"), "Verification changed tracked files; commit and verify the new snapshot")
    print("Local pre-push governance and verification passed.")


def pr_check(number):
    require(number.isdecimal() and int(number) > 0, "Provide PR_NUMBER=<number>")
    pr = json.loads(run("gh", "pr", "view", number, "--json", "title,body,headRefName,headRefOid,baseRefOid"))
    event = {"pull_request": {"title": pr["title"], "body": pr["body"], "head": {"ref": pr["headRefName"], "sha": pr["headRefOid"]}, "base": {"sha": pr["baseRefOid"]}}}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as file:
        json.dump(event, file)
        file.flush()
        subprocess.run([sys.executable, "scripts/validate_git_governance.py", "--event-file", file.name], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "commit-msg", "pre-push", "pr-check"))
    parser.add_argument("args", nargs="*")
    args = parser.parse_args()
    os.chdir(git("rev-parse", "--show-toplevel"))
    if args.action == "install":
        install()
    elif args.action == "commit-msg":
        commit_message(args.args[0])
    elif args.action == "pre-push":
        pre_push(args.args[0], sys.stdin.read())
    else:
        pr_check(args.args[0] if args.args else "")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, IndexError, subprocess.CalledProcessError) as error:
        print(f"Local Git check failed: {error}", file=sys.stderr)
        sys.exit(1)
