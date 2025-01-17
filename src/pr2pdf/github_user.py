from pydantic import BaseModel


class GitHubUser(BaseModel):
    """Class representing a GitHub user."""

    login: str
    html_url: str
