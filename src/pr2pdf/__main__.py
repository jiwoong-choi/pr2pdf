import argparse
import os
import subprocess
from datetime import datetime

import pdfkit

from . import PullRequest, collate_as_html


def main() -> None:
    """Process GitHub PRs and generate a combined PDF document.

    Command-line Arguments:
        pr_urls (list[str]): List of GitHub pull request URLs
        --token (str, optional): GitHub Personal Access Token.
            If not provided, will try GHP_TOKEN env var or GitHub CLI auth.
        --output-path (str, optional): Path where the PDF should be saved.
            If not provided, uses current date as filename.

    Creates:
        {output_path or current_date}.pdf: Combined PDF file containing all PR details
    """
    parser = argparse.ArgumentParser(
        description="Export multiple GitHub PR details to a single PDF.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "pr_urls",
        nargs="+",
        help="List of GitHub pull request URLs",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GHP_TOKEN"),
        help="GitHub Personal Access Token (optional if GHP_TOKEN env var is set, or will be redirected to GitHub CLI)",
    )
    parser.add_argument(
        "--output-path",
        required=False,
        help="Path where the PDF should be saved (defaults to current date)",
    )

    args = parser.parse_args()

    # Try to get token from environment variable if not provided
    if not args.token:
        args.token = get_token_from_gh_cli()

    # Fetch all pull requests
    pull_requests = []
    for pr_url in args.pr_urls:
        try:
            print(f"Fetching {pr_url} ...")
            pull_requests.append(PullRequest.fetch(pr_url, args.token))
        except ValueError as e:
            print(f"Error parsing URL {pr_url}: {e}")
        except Exception as e:
            print(f"Error processing {pr_url}: {e}")

    # Generate the combined PDF file
    if pull_requests:
        html_content = collate_as_html(pull_requests)
        output_path = write_as_pdf(html_content, output_path=args.output_path)
        print(f"PDF successfully generated: {output_path}")


def get_token_from_gh_cli() -> str:
    """Get GitHub token from GitHub CLI authentication.

    Attempts to get an authentication token from GitHub CLI.
    If not logged in, prompts user to authenticate.

    Returns:
        str: GitHub authentication token

    Raises:
        Exception: If:
            - GitHub CLI (gh) is not installed
            - User cancels authentication
            - Token retrieval fails
    """
    try:
        # Check if user is logged in
        login_check = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, text=True
        )
        if login_check.returncode != 0:
            print("GitHub CLI not logged in. Please authenticate first...")
            subprocess.run(["gh", "auth", "login"], check=True)

        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("Failed to get token from GitHub CLI")
        return result.stdout.strip()
    except FileNotFoundError:
        raise Exception("GitHub CLI (gh) not found. Please install it first.")


def write_as_pdf(html_content: str, *, output_path: str | None = None) -> str:
    """Write HTML content to a PDF file.

    Args:
        html_content (str): HTML content to convert to PDF
        output_path (str | None, optional): Path where the PDF should be saved.
            If None, uses the current date as filename. Defaults to None.

    Returns:
        str: Path to the generated PDF file

    Raises:
        RuntimeError: If PDF generation fails
    """
    if output_path is None:
        today = datetime.now().strftime("%Y-%m-%d")
        output_path = f"{today}.pdf"

    print(f"Writing PDF to {output_path} ...")
    if not pdfkit.from_string(html_content, output_path):
        raise RuntimeError("Failed to generate PDF")

    return output_path


if __name__ == "__main__":
    main()
