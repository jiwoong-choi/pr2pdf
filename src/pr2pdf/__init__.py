"""PR2PDF - Generate PDF documents from GitHub Pull Requests.

This package provides functionality to convert GitHub Pull Requests into PDF documents,
including PR details, file changes, and reviews.

Example:
    >>> import pr2pdf
    >>> pr2pdf.generate_pdf(
    ...     pr_urls=["https://github.com/owner/repo/pull/123"],
    ...     token="your_github_token"
    ... )
    'PDF successfully generated: 2024-02-20.pdf'

    # Or use environment variable GHP_TOKEN or GitHub CLI auth
    >>> pr2pdf.generate_pdf(["https://github.com/owner/repo/pull/123"])
"""

from .pull_request import PullRequest


def collate_as_html(pull_requests: list[PullRequest]) -> str:
    """Generate HTML content from GitHub Pull Requests.

    Args:
        pull_requests (list[PullRequest]): List of pull request objects

    Returns:
        str: Combined HTML content of all pull requests
    """
    return "".join(pr.to_html() for pr in pull_requests)


__version__ = "0.0.1"
__all__ = ["collate_as_html", "PullRequest"]
