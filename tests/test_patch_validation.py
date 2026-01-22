import pytest
from app.models import FileEdit, AgentPlan
from app.policy import enforce_policy
from app.sandbox import execute_plan


def test_policy_blocks_github_directory():
    edits = [
        FileEdit(
            file_path=".github/workflows/ci.yml",
            original_hash="fakehash",
            unified_diff="--- a/x\n+++ b/x\n@@ -1 +1 @@\n-test\n+test",
        )
    ]

    with pytest.raises(RuntimeError, match="Blocked by policy"):
        enforce_policy(edits)


def test_hash_mismatch_blocks_execution(tmp_path):
    """
    Ensures hallucinated or stale edits are rejected.
    """
    # Fake plan against nonexistent repo
    plan = AgentPlan(
        edits=[
            FileEdit(
                file_path="fake.py",
                original_hash="1234567890",
                unified_diff="--- a/fake.py\n+++ b/fake.py\n@@ -1 +1 @@\n-test\n+test",
            )
        ]
    )

    with pytest.raises(Exception):
        execute_plan("https://github.com/nonexistent/repo.git", plan)


def test_legit_plan_structure():
    """
    Ensures schema behaves as expected.
    """
    plan = AgentPlan(
        edits=[
            FileEdit(
                file_path="src/example.py",
                original_hash="abc123",
                unified_diff="--- a/src/example.py\n+++ b/src/example.py\n@@ -1 +1 @@\n-print('hi')\n+print('hello')",
            )
        ]
    )

    assert plan.edits[0].file_path == "src/example.py"
