"""Reading recipients from a public Google Sheet, via its CSV export."""
import csv
import re
from io import StringIO

import requests

# Longest aliases first so a "resume link" header beats a bare "link" during the
# substring pass, and "linkedin url" never gets mistaken for the resume column.
FIELD_ALIASES = {
    "email": ["email address", "hr email", "e-mail", "email", "mail"],
    "name": ["contact name", "full name", "hr name", "name"],
    "company": ["company name", "organisation", "organization", "company"],
    "job_position": ["job position", "job title", "designation", "position", "role"],
    "resume_link": ["resume link", "resume url", "cv link", "resume", "cv"],
}

SHEET_ID_PATTERNS = [
    r"/spreadsheets/d/([a-zA-Z0-9-_]+)",
    r"key=([a-zA-Z0-9-_]+)",
]


def _normalize(header):
    return header.strip().lower().replace("_", " ").replace("-", " ")


def _pick_column(headers, aliases):
    lookup = {_normalize(h): h for h in headers if h}

    for alias in aliases:
        if alias in lookup:
            return lookup[alias]

    for alias in aliases:
        for normalized, original in lookup.items():
            if alias in normalized:
                return original
    return None


class SheetsReader:
    def __init__(self, sheet_url=None):
        self.sheet_url = sheet_url

    def extract_sheet_id(self, url):
        for pattern in SHEET_ID_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError("That doesn't look like a Google Sheets URL.")

    def _csv_url(self, url):
        sheet_id = self.extract_sheet_id(url)
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        # Respect the tab the user actually copied the URL from.
        gid = re.search(r"[#&]gid=([0-9]+)", url)
        if gid:
            csv_url += f"&gid={gid.group(1)}"
        return csv_url

    def read_public_sheet(self, sheet_url=None):
        url = sheet_url or self.sheet_url
        if not url:
            raise ValueError("Sheet URL not provided")

        try:
            response = requests.get(self._csv_url(url), timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise Exception(
                f"Could not fetch the sheet ({exc}). Make sure it is shared as "
                "'Anyone with the link can view'."
            ) from exc

        # A sheet that isn't public redirects to an HTML sign-in page, which
        # csv.DictReader would happily parse into garbage rows.
        if "text/csv" not in response.headers.get("content-type", ""):
            raise Exception(
                "The sheet is not public. Open it, click Share, and set "
                "'Anyone with the link' to Viewer."
            )

        records = list(csv.DictReader(StringIO(response.text)))
        return [r for r in records if any((v or "").strip() for v in r.values())]

    def validate_records(self, records):
        """Map whatever the sheet's headers are onto our field names."""
        if not records:
            raise ValueError("The sheet is empty.")

        headers = list(records[0].keys())
        columns = {
            field: _pick_column(headers, aliases)
            for field, aliases in FIELD_ALIASES.items()
        }

        if not columns["email"]:
            raise ValueError(
                f"No email column found. Headers were: {', '.join(h for h in headers if h)}"
            )

        def value(record, field):
            column = columns[field]
            return (record.get(column) or "").strip() if column else ""

        normalized = []
        for record in records:
            email = value(record, "email")
            if not email:
                continue
            normalized.append(
                {
                    "name": value(record, "name") or "there",
                    "email": email,
                    "company": value(record, "company") or "your organization",
                    "job_position": value(record, "job_position") or None,
                    "resume_link": value(record, "resume_link") or None,
                }
            )

        if not normalized:
            raise ValueError("No rows with an email address were found.")

        return normalized
