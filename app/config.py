from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    workspace_root: str = "/tmp/safeagent"
    require_tests: bool = True

    # DB
    database_url: str = "postgresql://safeagent:safeagent@db:5432/safeagent"

    # GitHub
    github_token: str | None = None
    github_app_id: str | None = None
    github_private_key: str | None = None
    github_installation_id: str | None = None
    github_repo_owner: str | None = None
    github_repo_name: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )


settings = Settings()
