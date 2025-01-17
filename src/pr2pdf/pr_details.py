from typing import Any

from pydantic import BaseModel, Field, model_validator

from .github_user import GitHubUser
from .time import convert_to_kst


class PRDetails(BaseModel):
    """Class representing GitHub Pull Request details."""

    title: str
    body: str | None
    created_at: str
    user: GitHubUser
    api_url: str = Field(alias="_links")

    @model_validator(mode="before")
    def extract_api_url(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Extract api_url from _links structure before model creation."""
        if isinstance(values.get("_links"), dict):
            values["_links"] = values["_links"]["self"]["href"]
        return values

    @property
    def created_at_kst(self) -> str:
        """Get the created_at time in KST format."""
        return convert_to_kst(self.created_at)

    @property
    def author_login(self) -> str:
        """Get the author's login name."""
        return self.user.login

    @property
    def author_url(self) -> str:
        """Get the author's GitHub profile URL."""
        return self.user.html_url

    @property
    def files_url(self) -> str:
        """Get the URL for PR files."""
        return f"{self.api_url}/files"
