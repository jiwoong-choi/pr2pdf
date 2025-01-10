import argparse
import requests
import pdfkit
from bs4 import BeautifulSoup
from markdown import markdown  # To render Markdown as HTML
from datetime import datetime, timedelta

# Function to convert UTC to KST
def convert_to_kst(utc_datetime):
    utc_time = datetime.strptime(utc_datetime, "%Y-%m-%dT%H:%M:%SZ")
    kst_time = utc_time + timedelta(hours=9)  # KST is UTC+9
    return kst_time.strftime('%Y-%m-%d %H:%M:%S')

# Function to fetch PR data
def fetch_pr_data(repo, pr_number, token):
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

# Function to generate HTML content for a PR
def generate_html_for_pr(pr_details, files, reviewers):
    html_content = f"<h1>{pr_details['title']}</h1>"

    # Author, Created At, and Reviewers in a single box with light yellow background
    author_login = pr_details['user']['login']
    author_url = pr_details['user']['html_url']
    created_at_kst = convert_to_kst(pr_details["created_at"])
    reviewers_links = ", ".join(
        [f"<a href='https://github.com/{reviewer}'>{reviewer}</a>" for reviewer in reviewers]
    ) if reviewers else "No reviewers"
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
                formatted_patch += f"<span style='color: blue; font-weight: bold;'>{line}</span><br>"
            else:
                formatted_patch += f"{line}<br>"

        html_content += (
            f"<pre style='background-color: #f4f4f4; padding: 10px; border: 1px solid #ddd;'>"
            f"{formatted_patch}</pre>"
        )

    # Add a black divider at the end of the PR
    html_content += "<hr style='border: 2px solid black; margin: 40px 0;'>"
    return html_content

# Main function
def main():
    parser = argparse.ArgumentParser(description="Export multiple GitHub PR details to a single PDF.")
    parser.add_argument(
        "pr_list",
        nargs="+",
        help="List of pull requests in format {repo}:{pr_number}",
    )
    parser.add_argument("--token", required=True, help="GitHub Personal Access Token")

    args = parser.parse_args()
    token = args.token

    # Initialize HTML content for the combined PDF
    combined_html_content = ""

    for pr_item in args.pr_list:
        try:
            repo, pr_number = pr_item.split(":")
            pr_details, files, reviewers = fetch_pr_data(repo, pr_number, token)
            combined_html_content += generate_html_for_pr(pr_details, files, reviewers)
        except Exception as e:
            print(f"Error processing {pr_item}: {e}")

    # Generate the combined PDF file
    if combined_html_content:
        today = datetime.now().strftime("%Y-%m-%d")
        output_file = f"{today}.pdf"
        pdfkit.from_string(combined_html_content, output_file)
        print(f"PDF successfully generated: {output_file}")

if __name__ == "__main__":
    main()
