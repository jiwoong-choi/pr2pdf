# PR2PDF

Generate PDF documents from GitHub Pull Requests.

This package provides functionality to convert GitHub Pull Requests into PDF documents,
including PR details, file changes, and reviews.

## Features

- Convert one or multiple GitHub PRs to a single PDF document
- Include PR details like title, description, author, and timestamps
- Support for file changes with syntax highlighting
- Show reviewers and their GitHub profiles
- Multiple authentication methods:
  - GitHub Personal Access Token
  - Environment variable (GHP_TOKEN)
  - GitHub CLI authentication

## Requirements

- Python 3.10 or higher
- wkhtmltopdf - Required for PDF generation. Install using:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install wkhtmltopdf

  # macOS
  brew install wkhtmltopdf

  # Windows
  choco install wkhtmltopdf
  ```
- GitHub CLI (optional) - For CLI-based authentication

## Environment Setup

You can set up the development environment using conda or mamba:

```bash
# Using conda
conda env create -f environment.yaml
conda activate pr2pdf

# Using mamba
mamba env create -f environment.yaml
mamba activate pr2pdf
```

This will create a new environment with all the required dependencies installed.

## Installation

You can install PR2PDF using pip:

```bash
pip install git+https://github.com/jiwoong-choi/pr2pdf.git
```

## Usage

### Command Line Interface

Basic usage with GitHub CLI authentication:
```bash
pr2pdf https://github.com/owner/repo/pull/123
```

Using a personal access token:
```bash
pr2pdf https://github.com/owner/repo/pull/123 --token YOUR_GITHUB_TOKEN
```

Multiple PRs with custom output path:
```bash
pr2pdf https://github.com/owner/repo/pull/123 https://github.com/owner/repo/pull/456 --output-path my_prs.pdf
```

### Python API

```python
import pr2pdf

# Using GitHub token
pr2pdf.generate_pdf(
    pr_urls=["https://github.com/owner/repo/pull/123"],
    token="your_github_token"
)

# Using GitHub CLI auth (token will be retrieved automatically)
pr2pdf.generate_pdf(["https://github.com/owner/repo/pull/123"])
```

## Output Format

The generated PDF includes:
- PR title and metadata
- Author information with GitHub profile link
- Creation timestamp (in KST)
- List of reviewers with GitHub profile links
- PR description (rendered from Markdown)
- File changes with syntax highlighting:
  - Added lines in green
  - Removed lines in red
  - Change markers in blue

## Authentication

PR2PDF supports three authentication methods, tried in the following order:

1. `--token` command line argument
2. `GHP_TOKEN` environment variable
3. GitHub CLI authentication (requires `gh` CLI to be installed and authenticated)

To use GitHub CLI authentication:
```bash
gh auth login
pr2pdf https://github.com/owner/repo/pull/123
```

## License

MIT License
