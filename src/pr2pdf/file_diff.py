import re
from typing import Optional

from pydantic import BaseModel


class FileDiff(BaseModel):
    """Class representing a file difference in a pull request."""

    filename: str
    status: str  # added/modified/removed
    patch: Optional[str] = None

    def to_html(self) -> str:
        """Convert the file diff to a GitHub-style HTML format."""
        status_colors = {
            "added": "#28a745",
            "modified": "#dbab09",
            "removed": "#d73a49",
            "renamed": "#007bff",
        }
        status_style = (
            f"color: {status_colors.get(self.status, '#000')}; font-weight: bold;"
        )

        html = f"""
        <div style="border: 1px solid #ddd; border-radius: 6px; margin-bottom: 16px; font-family: monospace;">
            <div style="background-color: #f6f8fa; padding: 8px 16px; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center;">
                <strong style="font-size: 14px;">{self.filename}</strong>
                <span style="{status_style}">{self.status.capitalize()}</span>
            </div>
        """

        if not self.patch:
            html += "</div>"
            return html

        html += '<table style="width: 100%; border-collapse: collapse;"><tbody>'

        old_line_num = 0
        new_line_num = 0
        hunk_started = False

        for line in self.patch.split('\n'):
            if line.startswith("@@"):
                hunk_started = True
                match = re.search(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
                if match:
                    old_line_num = int(match.group(1))
                    new_line_num = int(match.group(2))
                else:
                    old_line_num = 0
                    new_line_num = 0

                html += f"""
                <tr>
                    <td colspan="2" style="background-color: #f1f8ff; color: #586069; padding: 4px 8px; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd; width: 80px;">...</td>
                    <td style="background-color: #f1f8ff; color: #586069; padding: 4px 8px; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd;"><pre style="margin: 0;">{line}</pre></td>
                </tr>
                """
            elif hunk_started:
                if line.startswith("+") and not line.startswith("+++"):
                    html += f"""
                    <tr>
                        <td style="background-color: #cdffd8; text-align: right; padding: 0 8px; color: #586069; width: 40px;"></td>
                        <td style="background-color: #cdffd8; text-align: right; padding: 0 8px; color: #586069; width: 40px;">{new_line_num}</td>
                        <td style="background-color: #e6ffed; padding: 0 8px;"><pre style="margin: 0; color: #24292e;">{line}</pre></td>
                    </tr>
                    """
                    new_line_num += 1
                elif line.startswith("-") and not line.startswith("---"):
                    html += f"""
                    <tr>
                        <td style="background-color: #ffdce0; text-align: right; padding: 0 8px; color: #586069; width: 40px;">{old_line_num}</td>
                        <td style="background-color: #ffdce0; text-align: right; padding: 0 8px; color: #586069; width: 40px;"></td>
                        <td style="background-color: #ffeef0; padding: 0 8px;"><pre style="margin: 0; color: #24292e;">{line}</pre></td>
                    </tr>
                    """
                    old_line_num += 1
                elif line.startswith(" "):
                    html += f"""
                    <tr>
                        <td style="text-align: right; padding: 0 8px; color: #586069; width: 40px;">{old_line_num}</td>
                        <td style="text-align: right; padding: 0 8px; color: #586069; width: 40px;">{new_line_num}</td>
                        <td style="padding: 0 8px;"><pre style="margin: 0; color: #24292e;">{line}</pre></td>
                    </tr>
                    """
                    old_line_num += 1
                    new_line_num += 1
                elif line == "\\ No newline at end of file":
                    html += f"""
                    <tr>
                        <td colspan="2" style="background-color: #fafbfc; color: #586069; padding: 4px 8px; border-top: 1px solid #ddd; width: 80px;"></td>
                        <td style="background-color: #fafbfc; color: #586069; padding: 4px 8px; border-top: 1px solid #ddd;"><pre style="margin: 0;">{line}</pre></td>
                    </tr>
                    """

        html += "</tbody></table></div>"
        return html
