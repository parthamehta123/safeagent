import subprocess, tempfile


def apply_patch(repo_path: str, unified_diff: str):
    import tempfile
    import subprocess

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(unified_diff)
        patch_file = f.name

    try:
        subprocess.check_output(
            [
                "git",
                "apply",
                "--recount",
                "--unidiff-zero",
                "--whitespace=fix",
                patch_file,
            ],
            cwd=repo_path,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.output.decode())
