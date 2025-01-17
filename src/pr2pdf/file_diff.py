from typing import Optional

from pydantic import BaseModel


class FileDiff(BaseModel):
    """Class representing a file difference in a pull request."""

    filename: str
    status: str  # added/modified/removed
    patch: Optional[str] = None

    def to_html(self) -> str:
        """Convert the file diff to HTML format.

        Returns:
            str: HTML representation of the file diff with:
                - Filename as header
                - Status information
                - Colored diff content (if patch exists)
        """
        html = f"<h3>{self.filename}</h3>"
        html += f"<p><strong>Status:</strong> {self.status}</p>"

        if self.patch:
            formatted_patch = ""
            for line in self.patch.split("\n"):
                if line.startswith("+") and not line.startswith("+++"):
                    formatted_patch += f"<span style='color: green;'>{line}</span><br>"
                elif line.startswith("-") and not line.startswith("---"):
                    formatted_patch += f"<span style='color: red;'>{line}</span><br>"
                elif line.startswith("@@"):
                    formatted_patch += f"<span style='color: blue; font-weight: bold;'>{line}</span><br>"
                else:
                    formatted_patch += f"{line}<br>"

            html += (
                f"<pre style='background-color: #f4f4f4; padding: 10px; border: 1px solid #ddd;'>"
                f"{formatted_patch}</pre>"
            )

        return html
