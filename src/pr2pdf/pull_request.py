import requests
from markdown import markdown
from pydantic import BaseModel
from typing_extensions import Self

from .commit import Commit
from .file_diff import FileDiff
from .github_user import GitHubUser
from .pr_details import PRDetails
from .time import Time


class PullRequest(BaseModel):
    """Class representing a complete GitHub Pull Request with all its data."""

    details: PRDetails
    files: list[FileDiff]
    reviewers: set[str]
    commits: list[Commit]

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
        files_url = f"{base_url}/files"
        files = []
        page = 1
        while True:
            files_response = requests.get(
                files_url, headers=headers, params={"per_page": 100, "page": page}
            )
            if files_response.status_code != 200:
                raise Exception(f"Failed to fetch PR files: {files_response.json()}")
            
            page_files = files_response.json()
            if not page_files:
                break
            
            files.extend([FileDiff.model_validate(file) for file in page_files])
            page += 1

        # Fetch reviewers
        reviews_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
        reviews_response = requests.get(reviews_url, headers=headers)
        if reviews_response.status_code != 200:
            raise Exception(f"Failed to fetch PR reviews: {reviews_response.json()}")

        reviews = reviews_response.json()
        reviewers = {review["user"]["login"] for review in reviews}

        # Fetch commits
        commits_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/commits"
        commits_response = requests.get(commits_url, headers=headers)
        if commits_response.status_code != 200:
            raise Exception(f"Failed to fetch PR commits: {commits_response.json()}")

        commits_data = commits_response.json()
        commits = [
            Commit(
                sha=commit["sha"],
                message=commit["commit"]["message"],
                author=GitHubUser(
                    login=commit["author"]["login"],
                    html_url=commit["author"]["html_url"],
                ),
                date=Time(commit["commit"]["author"]["date"]),
            )
            for commit in commits_data
        ]

        return cls(
            details=pr_details,
            files=files,
            reviewers=reviewers,
            commits=commits,
        )

    def to_html(self) -> str:
        """Generate HTML content for the pull request.

        Returns:
            str: HTML string containing formatted PR information with:
                - Title and metadata (author, date, reviewers)
                - PR description in Markdown
                - File changes with syntax highlighting
        """
        markdown_styles = """
            <style>
                .markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4, .markdown-body h5, .markdown-body h6 {
                    border-bottom: 1px solid #eaecef;
                    padding-bottom: .3em;
                }
                .markdown-body ul {
                    list-style-type: disc;
                    list-style-position: inside;
                }
                .markdown-body ol {
                    list-style-type: decimal;
                    list-style-position: inside;
                }
                .markdown-body ul, .markdown-body ol {
                    padding-left: 2em;
                }
                .markdown-body blockquote {
                    border-left: .25em solid #dfe2e5;
                    color: #6a737d;
                    padding: 0 1em;
                    margin-left: 0;
                }
                .markdown-body pre {
                    background-color: #f6f8fa;
                    border-radius: 3px;
                    font-size: 85%;
                    line-height: 1.45;
                    overflow: auto;
                    padding: 16px;
                }
                .markdown-body code {
                    background-color: rgba(27,31,35,.05);
                    border-radius: 3px;
                    font-size: 85%;
                    margin: 0;
                    padding: .2em .4em;
                }
                .markdown-body pre > code {
                    background-color: transparent;
                    font-size: 100%;
                    margin: 0;
                    padding: 0;
                    border: 0;
                }
            </style>
        """

        html_content = f"<h1>{self.details.title}</h1>"

        # Author, Created At, and Reviewers in a single box
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
            f"<div style='background-color: #f6f8fa; padding: 15px; border: 1px solid #ddd; border-radius: 6px; margin-bottom: 20px;'>"
            f"<p><strong>Author:</strong> <a href='{self.details.author_url}'>{self.details.author_login}</a></p>"
            f"<p><strong>Reviewers:</strong> {reviewers_links}</p>"
            f"</div>"
        )

        # Render Markdown in the "Overview" section
        pr_description_html = ""
        if self.details.body:
            body_parts = self.details.body.split("Key Changes:")
            pr_description_html = markdown(body_parts[0], extensions=["extra"])

            if len(body_parts) > 1:
                key_changes_content = body_parts[1].strip()
                key_changes_lines = key_changes_content.split('\n')
                key_changes_html_list = []
                for line in key_changes_lines:
                    stripped_line = line.strip()
                    if stripped_line.startswith('*'):
                        key_changes_html_list.append(f"<li>{stripped_line[1:].strip()}</li>")
                    else:
                        key_changes_html_list.append(f"<p>{stripped_line}</p>") # Handle non-list lines
                
                if key_changes_html_list:
                    pr_description_html += "<h3>Key Changes:</h3><ul>" + "".join(key_changes_html_list) + "</ul>"
                else:
                    pr_description_html += f"<h3>Key Changes:</h3><p>{key_changes_content}</p>"
        
        commit_html_list = []
        for commit in self.commits:
            lines = commit.message.strip().split('\n')
            subject = lines[0]
            body_lines = lines[1:]

            commit_item_html = f"<li>{subject} - <small><a href='{commit.author.html_url}'>{commit.author.login}</a> ({commit.date.to_kst_str()})</small>"
            if body_lines:
                body = '\n'.join(filter(str.strip, body_lines))
                if body:
                    commit_item_html += f"<pre style=\"margin-left: 2em;\">{body}</pre>"
            commit_item_html += "</li>"
            commit_html_list.append(commit_item_html)

        commit_messages_html = f"<h3>Commits</h3><ul>{''.join(commit_html_list)}</ul>"

        body_html = pr_description_html + commit_messages_html
        html_content += "<h2>Overview</h2>"
        html_content += "<hr style='border: 1px solid #ddd; margin: 10px 0;'>"
        html_content += (
            f"<div class='markdown-body' style='background-color: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 6px; margin-bottom: 20px;'>"
            f"{markdown_styles}{body_html}</div>"
        )

        html_content += "<h2>Files Changed</h2>"
        html_content += "<hr style='border: 1px solid #ddd; margin: 10px 0;'>"

        for file in self.files:
            html_content += file.to_html()

        # Add a black divider at the end of the PR
        html_content += "<hr style='border: 2px solid black; margin: 40px 0;'>"
        return html_content