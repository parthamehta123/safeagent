FORBIDDEN_PATHS = [".github/", "infra/", "terraform/"]


def enforce_policy(edits):
    for e in edits:
        for bad in FORBIDDEN_PATHS:
            if e.file_path.startswith(bad):
                raise RuntimeError(f"Blocked by policy: {e.file_path}")


def validate_diff_safety(diff: str, max_deletions: int = 200):
    """
    Prevent catastrophic deletions even if tests pass.
    """
    deletions = sum(
        1
        for line in diff.splitlines()
        if line.startswith("-") and not line.startswith("---")
    )

    if deletions > max_deletions:
        raise RuntimeError(
            f"Unsafe diff: deletes too many lines ({deletions} > {max_deletions})"
        )
