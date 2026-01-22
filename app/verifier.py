import subprocess
import ast
import os
from app.config import settings


def run_ast_checks(repo_path: str):
    for root, _, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as fp:
                        ast.parse(fp.read())
                except Exception as e:
                    raise RuntimeError(f"AST error in {path}: {e}")


def run_tests(repo_path: str):
    # Respect config
    if not settings.require_tests:
        return

    has_tests = (
        os.path.exists(os.path.join(repo_path, "tests"))
        or os.path.exists(os.path.join(repo_path, "pytest.ini"))
        or os.path.exists(os.path.join(repo_path, "pyproject.toml"))
    )

    if not has_tests:
        return

    result = subprocess.run(
        ["pytest", "-q"],
        cwd=repo_path,
    )

    if result.returncode != 0:
        raise RuntimeError("Tests failed")
