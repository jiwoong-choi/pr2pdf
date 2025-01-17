import requests
from pydantic import BaseModel
from typing_extensions import Self

from .file_diff import FileDiff
from .pr_details import PRDetails


class PullRequest(BaseModel):
    """Class representing a complete GitHub Pull Request with all its data."""

    details: PRDetails
    files: list[FileDiff]
    reviewers: set[str]

    @staticmethod
    def parse_url(url: str) -> tuple[str, str]:
        """Parse GitHub pull request URL to extract repository and PR number.

        Args:
            url (str): GitHub pull request URL in format:
                https://github.com/owner/repo/pull/number
                Trailing slashes and additional paths are ignored

        Returns:
            tuple[str, str]: Tuple containing:
                - repo_path (str): Repository path in format "owner/repo"
                - pr_number (str): Pull request number

        Raises:
            ValueError: If URL format is invalid, with explanation
        """
        try:
            # Remove trailing slash if present
            url = url.rstrip("/")

            # Split URL into parts
            parts = url.split("/")

            # Basic validation
            if len(parts) < 7 or parts[2] != "github.com" or parts[5] != "pull":
                raise ValueError

            repo = f"{parts[3]}/{parts[4]}"
            pr_number = parts[6]

            return repo, pr_number

        except (IndexError, ValueError):
            raise ValueError(
                "Invalid GitHub PR URL. Expected format: "
                "https://github.com/owner/repo/pull/number"
            )

    @classmethod
    def fetch(cls, pr_url: str, token: str) -> Self:
        """Fetch pull request data from GitHub API.

        Args:
            pr_url (str): GitHub pull request URL
            token (str): GitHub personal access token

        Returns:
            Self: Complete pull request data including details, files, and reviewers

        Raises:
            ValueError: If URL format is invalid
            Exception: If any GitHub API requests fail with error details
        """
        repo, pr_number = cls.parse_url(pr_url)
        headers = {"Authorization": f"token {token}"}
        base_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"

        # Fetch PR details
        pr_response = requests.get(base_url, headers=headers)
        if pr_response.status_code != 200:
            raise Exception(f"Failed to fetch PR details: {pr_response.json()}")

        pr_details = PRDetails.model_validate(pr_response.json())

        # Fetch files from the "Files changed" tab
        files_response = requests.get(pr_details.files_url, headers=headers)
        if files_response.status_code != 200:
            raise Exception(f"Failed to fetch PR files: {files_response.json()}")

        files = [FileDiff.model_validate(file) for file in files_response.json()]

        # Fetch reviewers
        reviews_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
        reviews_response = requests.get(reviews_url, headers=headers)
        if reviews_response.status_code != 200:
            raise Exception(f"Failed to fetch PR reviews: {reviews_response.json()}")

        reviews = reviews_response.json()
        reviewers = {review["user"]["login"] for review in reviews}

        return cls(details=pr_details, files=files, reviewers=reviewers)

    def to_html(self) -> str:
        """Generate HTML content for the pull request.

        Returns:
            str: HTML string containing formatted PR information with:
                - Title and metadata (author, date, reviewers)
                - PR description in Markdown
                - File changes with syntax highlighting
        """
        from markdown import markdown

        html_content = f"<h1>{self.details.title}</h1>"

        # Author, Created At, and Reviewers in a single box with light yellow background
        reviewers_links = (
            ", ".join(
                [
                    f"<a href='https://github.com/{reviewer}'>{reviewer}</a>"
                    for reviewer in self.reviewers
                ]
            )
            if self.reviewers
            else "No reviewers"
        )
        html_content += (
            f"<div style='background-color: #fff8dc; padding: 15px; border: 1px solid #ccc; border-radius: 5px; margin-bottom: 20px;'>"
            f"<p><strong>Author:</strong> <a href='{self.details.author_url}'>{self.details.author_login}</a></p>"
            f"<p><strong>Created At (KST):</strong> {self.details.created_at_kst}</p>"
            f"<p><strong>Reviewers:</strong> {reviewers_links}</p>"
            f"</div>"
        )

        # Render Markdown in the "Overview" section
        if self.details.body:
            body_html = markdown(self.details.body)
            html_content += "<h2>Overview</h2>"
            html_content += "<hr style='border: 1px solid #ddd; margin: 10px 0;'>"
            html_content += (
                f"<div style='background-color: #f4f4f4; padding: 10px; border: 1px solid #ddd; border-radius: 5px;'>"
                f"{body_html}</div>"
            )

        html_content += "<h2>Files Changed</h2>"
        html_content += "<hr style='border: 1px solid #ddd; margin: 10px 0;'>"

        for file in self.files:
            html_content += file.to_html()

        # Add a black divider at the end of the PR
        html_content += "<hr style='border: 2px solid black; margin: 40px 0;'>"
        return html_content
