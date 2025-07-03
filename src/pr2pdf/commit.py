from dataclasses import dataclass

from .github_user import GitHubUser
from .time import Time


@dataclass
class Commit:
    """Represents a single commit in a pull request."""

    sha: str
    message: str
    author: GitHubUser
    date: Time
