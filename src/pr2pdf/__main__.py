import argparse
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Set, Tuple

import pdfkit
import requests
from markdown import markdown  # To render Markdown as HTML


def convert_to_kst(utc_datetime: str) -> str:
    """Convert UTC datetime string to KST datetime string.

    Args:
        utc_datetime: UTC datetime string in format "YYYY-MM-DDTHH:MM:SSZ"

    Returns:
        KST datetime string in format "YYYY-MM-DD HH:MM:SS"
    """
    utc_time = datetime.strptime(utc_datetime, "%Y-%m-%dT%H:%M:%SZ")
    kst_time = utc_time + timedelta(hours=9)  # KST is UTC+9
    return kst_time.strftime("%Y-%m-%d %H:%M:%S")


def fetch_pr_data(
    repo: str, pr_number: str, token: str
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Set[str]]:
    """Fetch pull request data from GitHub API.

    Args:
        repo: GitHub repository in format "owner/repo"
        pr_number: Pull request number
        token: GitHub personal access token

    Returns:
        Tuple containing:
            - PR details dictionary
            - List of changed files
            - Set of reviewer usernames

    Raises:
        Exception: If any API requests fail
    """
    headers = {"Authorization": f"token {token}"}
    base_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"

    # Fetch PR details
    pr_response = requests.get(base_url, headers=headers)
    if pr_response.status_code != 200:
        raise Exception(f"Failed to fetch PR details: {pr_response.json()}")

    pr_details = pr_response.json()

    # Fetch files from the "Files changed" tab
    files_url = pr_details["_links"]["self"]["href"] + "/files"
    files_response = requests.get(files_url, headers=headers)
    if files_response.status_code != 200:
        raise Exception(f"Failed to fetch PR files: {files_response.json()}")

    files = files_response.json()

    # Fetch reviewers
    reviews_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    reviews_response = requests.get(reviews_url, headers=headers)
    if reviews_response.status_code != 200:
        raise Exception(f"Failed to fetch PR reviews: {reviews_response.json()}")

    reviews = reviews_response.json()
    reviewers = set(review["user"]["login"] for review in reviews)

    return pr_details, files, reviewers


def generate_html_for_pr(
    pr_details: Dict[str, Any], files: List[Dict[str, Any]], reviewers: Set[str]
) -> str:
    """Generate HTML content for a pull request.

    Args:
        pr_details: Dictionary containing PR details from GitHub API
        files: List of changed files from GitHub API
        reviewers: Set of reviewer usernames

    Returns:
        HTML string containing formatted PR information
    """
    html_content = f"<h1>{pr_details['title']}</h1>"

    # Author, Created At, and Reviewers in a single box with light yellow background
    author_login = pr_details["user"]["login"]
    author_url = pr_details["user"]["html_url"]
    created_at_kst = convert_to_kst(pr_details["created_at"])
    reviewers_links = (
        ", ".join(
            [
                f"<a href='https://github.com/{reviewer}'>{reviewer}</a>"
                for reviewer in reviewers
            ]
        )
        if reviewers
        else "No reviewers"
    )
    html_content += (
        f"<div style='background-color: #fff8dc; padding: 15px; border: 1px solid #ccc; border-radius: 5px; margin-bottom: 20px;'>"
        f"<p><strong>Author:</strong> <a href='{author_url}'>{author_login}</a></p>"
        f"<p><strong>Created At (KST):</strong> {created_at_kst}</p>"
        f"<p><strong>Reviewers:</strong> {reviewers_links}</p>"
        f"</div>"
    )

    # Render Markdown in the "Overview" section
    if pr_details.get("body"):
        body_html = markdown(pr_details["body"])
        html_content += "<h2>Overview</h2>"
        html_content += "<hr style='border: 1px solid #ddd; margin: 10px 0;'>"
        html_content += (
            f"<div style='background-color: #f4f4f4; padding: 10px; border: 1px solid #ddd; border-radius: 5px;'>"
            f"{body_html}</div>"
        )

    html_content += "<h2>Files Changed</h2>"
    html_content += "<hr style='border: 1px solid #ddd; margin: 10px 0;'>"
    for file in files:
        html_content += f"<h3>{file['filename']}</h3>"
        html_content += f"<p><strong>Status:</strong> {file['status']}</p>"

        # Format the diff with green for added lines, red for removed lines, and blue for diff headers
        patch = file.get("patch", "")
        formatted_patch = ""
        for line in patch.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                formatted_patch += f"<span style='color: green;'>{line}</span><br>"
            elif line.startswith("-") and not line.startswith("---"):
                formatted_patch += f"<span style='color: red;'>{line}</span><br>"
            elif line.startswith("@@"):
                formatted_patch += (
                    f"<span style='color: blue; font-weight: bold;'>{line}</span><br>"
                )
            else:
                formatted_patch += f"{line}<br>"

        html_content += (
            f"<pre style='background-color: #f4f4f4; padding: 10px; border: 1px solid #ddd;'>"
            f"{formatted_patch}</pre>"
        )

    # Add a black divider at the end of the PR
    html_content += "<hr style='border: 2px solid black; margin: 40px 0;'>"
    return html_content


def parse_github_pr_url(url: str) -> Tuple[str, str]:
    """Parse GitHub pull request URL to extract repository and PR number.

    Args:
        url: GitHub pull request URL in format:
            https://github.com/owner/repo/pull/number

    Returns:
        Tuple containing (repo_path, pr_number)

    Raises:
        ValueError: If URL format is invalid
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


def get_token_from_gh_cli() -> str:
    """Get GitHub token from GitHub CLI authentication.

    Returns:
        GitHub token string

    Raises:
        Exception: If gh cli is not installed or not authenticated
    """
    try:
        import subprocess

        # Check if user is logged in
        login_check = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        if login_check.returncode != 0:
            print("GitHub CLI not logged in. Please authenticate first...")
            subprocess.run(["gh", "auth", "login"], check=True)
        
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("Failed to get token from GitHub CLI")
        return result.stdout.strip()
    except FileNotFoundError:
        raise Exception("GitHub CLI (gh) not found. Please install it first.")


def main() -> None:
    """Main function to process GitHub PRs and generate PDF.

    Parses command line arguments, fetches PR data from GitHub,
    generates HTML content and converts it to PDF.
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

    args = parser.parse_args()

    # Try to get token from environment variable if not provided
    if not args.token:
        args.token = get_token_from_gh_cli()

    # Initialize HTML content for the combined PDF
    combined_html_content = ""

    for pr_url in args.pr_urls:
        try:
            repo, pr_number = parse_github_pr_url(pr_url)
            pr_details, files, reviewers = fetch_pr_data(repo, pr_number, args.token)
            combined_html_content += generate_html_for_pr(pr_details, files, reviewers)
        except ValueError as e:
            print(f"Error parsing URL {pr_url}: {e}")
        except Exception as e:
            print(f"Error processing {pr_url}: {e}")

    # Generate the combined PDF file
    if combined_html_content:
        today = datetime.now().strftime("%Y-%m-%d")
        output_file = f"{today}.pdf"
        pdfkit.from_string(combined_html_content, output_file)
        print(f"PDF successfully generated: {output_file}")


if __name__ == "__main__":
    main()
