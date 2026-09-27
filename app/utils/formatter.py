"""Format query results for the UI."""

from __future__ import annotations

import csv
import io
from typing import Any


def rows_to_html_table(rows: list[dict[str, Any]]) -> str:
    """Convert a list of mapping-like rows into an HTML table."""
    if not rows:
        return "<p class='empty-results'>No rows returned.</p>"

    headers = list(rows[0].keys())
    html = ["<div class='table-wrap'><table class='results-table'><thead><tr>"]
    for header in headers:
        html.append(f"<th>{header}</th>")
    html.append("</tr></thead><tbody>")
    for row in rows:
        html.append("<tr>")
        for header in headers:
            value = row[header]
            if value is None:
                display = "<span class='null'>NULL</span>"
            else:
                display = str(value)
            html.append(f"<td>{display}</td>")
        html.append("</tr>")
    html.append("</tbody></table></div>")
    return "".join(html)


def rows_to_csv(rows: list[dict[str, Any]]) -> str:
    """Convert rows to CSV text."""
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
