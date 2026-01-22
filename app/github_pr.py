import base64
import json
import time
import requests
import jwt
from app.config import settings


class GitHubPRClient:
    """
    Safe GitHub client:
    - Never writes to main
    - Always creates a new branch
    - Only opens PRs
    - No delete operations
    """

    def __init__(self):
        self.owner = settings.github_repo_owner
        self.repo = settings.github_repo_name
        self.base_branch = "main"

        if not self.owner or not self.repo:
            raise ValueError("GitHub repo owner/name not configured")

    # ---------------------------
    # AUTH
    # ---------------------------

    def _get_headers(self):
        token = self._get_installation_token()
        return {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        }

    def _get_installation_token(self) -> str:
        """
        Uses GitHub App authentication if configured.
        Falls back to GITHUB_TOKEN if provided.
        """

        # Local dev fallback
        if getattr(settings, "github_token", None):
            return settings.github_token

        if not all(
            [
                settings.github_app_id,
                settings.github_private_key,
                settings.github_installation_id,
            ]
        ):
            raise RuntimeError("GitHub auth not configured")

        now = int(time.time())

        payload = {
            "iat": now - 60,
            "exp": now + 600,
            "iss": settings.github_app_id,
        }

        private_key = settings.github_private_key.replace("\\n", "\n")
        jwt_token = jwt.encode(payload, private_key, algorithm="RS256")

        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
        }

        url = f"https://api.github.com/app/installations/{settings.github_installation_id}/access_tokens"
        resp = requests.post(url, headers=headers, timeout=10)

        if resp.status_code != 201:
            raise RuntimeError(f"GitHub token error: {resp.text}")

        return resp.json()["token"]

    # ---------------------------
    # CORE OPERATIONS
    # ---------------------------

    def create_branch(self, branch_name: str) -> str:
        """
        Creates new branch from main.
        """
        headers = self._get_headers()

        ref_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/git/ref/heads/{self.base_branch}"
        ref_resp = requests.get(ref_url, headers=headers)

        if ref_resp.status_code != 200:
            raise RuntimeError(f"Failed to get base ref: {ref_resp.text}")

        sha = ref_resp.json()["object"]["sha"]

        create_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/git/refs"
        payload = {"ref": f"refs/heads/{branch_name}", "sha": sha}

        create_resp = requests.post(create_url, headers=headers, json=payload)

        if create_resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to create branch: {create_resp.text}")

        return branch_name

    def commit_file(self, branch: str, file_path: str, new_content: str, message: str):
        """
        Safely updates a file in a branch.
        """
        headers = self._get_headers()

        get_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{file_path}?ref={branch}"
        get_resp = requests.get(get_url, headers=headers)

        sha = None
        if get_resp.status_code == 200:
            sha = get_resp.json()["sha"]

        encoded = base64.b64encode(new_content.encode()).decode()

        put_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{file_path}"
        payload = {
            "message": message,
            "content": encoded,
            "branch": branch,
        }

        if sha:
            payload["sha"] = sha

        put_resp = requests.put(put_url, headers=headers, json=payload)

        if put_resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to commit file: {put_resp.text}")

    def open_pull_request(self, branch: str, title: str, body: str = "") -> str:
        """
        Opens PR into main.
        """
        headers = self._get_headers()

        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls"
        payload = {
            "title": title,
            "head": branch,
            "base": self.base_branch,
            "body": body or "Created by SafeAgent",
        }

        resp = requests.post(url, headers=headers, json=payload)

        if resp.status_code != 201:
            raise RuntimeError(f"Failed to open PR: {resp.text}")

        return resp.json()["html_url"]

    def comment_on_pr(self, pr_url: str, body: str):
        headers = self._get_headers()

        # Extract PR number
        pr_number = pr_url.rstrip("/").split("/")[-1]

        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues/{pr_number}/comments"

        payload = {"body": body}
        resp = requests.post(url, headers=headers, json=payload)

        if resp.status_code != 201:
            raise RuntimeError(f"Failed to comment on PR: {resp.text}")
