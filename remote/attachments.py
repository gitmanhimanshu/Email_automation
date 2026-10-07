"""PDF attachment resolver and downloader for email applications.

Fetches PDF files from Google Drive URLs, direct web links, or local file paths,
and packages them for MIME attachment without requiring extra Google Drive API scopes.
"""
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx

_DRIVE_ID_RE = re.compile(r"/d/([a-zA-Z0-9_-]+)")


def extract_drive_id(url: str) -> str | None:
    """Extracts the Google Drive / Docs file ID from a URL."""
    if not url:
        return None
    match = _DRIVE_ID_RE.search(url)
    if match:
        return match.group(1)

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "id" in qs and qs["id"]:
        return qs["id"][0]
    return None


def format_pdf_filename(user_name: str | None = None) -> str:
    """Generate a clean, recruiter-friendly filename e.g. Resume_Himanshu_Yadav.pdf."""
    if not user_name:
        return "Resume.pdf"
    clean = re.sub(r"[^\w\s-]", "", user_name).strip()
    clean = re.sub(r"[-\s]+", "_", clean)
    return f"Resume_{clean}.pdf" if clean else "Resume.pdf"


async def fetch_pdf(url_or_path: str, user_name: str | None = None) -> tuple[bytes | None, str | None, str | None]:
    """Fetch PDF bytes from a Google Drive link, generic URL, or local file.

    Returns: (pdf_bytes, filename, error_message)
    """
    target = (url_or_path or "").strip()
    if not target:
        return None, None, "No resume link or file path provided."

    filename = format_pdf_filename(user_name)

    # 1. Check if it is a local file
    try:
        local_p = Path(target)
        if local_p.is_file():
            content = local_p.read_bytes()
            if len(content) > 0:
                return content, local_p.name or filename, None
    except Exception:
        pass

    # 2. Must be an HTTP(S) URL
    if not target.startswith(("http://", "https://")):
        return None, None, f"Unsupported link or file path: {target}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # 3. Google Drive / Docs handling
    drive_id = extract_drive_id(target)
    download_urls = []
    if drive_id:
        if "docs.google.com/document" in target:
            download_urls.append(f"https://docs.google.com/document/d/{drive_id}/export?format=pdf")
        download_urls.extend([
            f"https://drive.usercontent.google.com/download?id={drive_id}&export=download&authuser=0",
            f"https://drive.google.com/uc?export=download&id={drive_id}",
        ])
    else:
        # Generic URL (e.g. Dropbox dl=1)
        if "dropbox.com" in target and "?dl=0" in target:
            target = target.replace("?dl=0", "?dl=1")
        download_urls.append(target)

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=headers) as client:
        for d_url in download_urls:
            try:
                res = await client.get(d_url)
                if res.status_code == 200 and len(res.content) > 100:
                    content_type = res.headers.get("content-type", "").lower()
                    # Check for PDF header or content-type
                    if res.content.startswith(b"%PDF") or "application/pdf" in content_type or "octet-stream" in content_type:
                        return res.content, filename, None
                    # Fallback if binary file downloaded
                    if len(res.content) > 1000 and b"<!DOCTYPE html" not in res.content[:200]:
                        return res.content, filename, None
            except Exception:
                continue

    return None, None, "Could not download a valid PDF from the provided link."


def fetch_pdf_sync(url_or_path: str, user_name: str | None = None) -> tuple[bytes | None, str | None, str | None]:
    """Synchronous version of fetch_pdf for CLI and stdio servers."""
    target = (url_or_path or "").strip()
    if not target:
        return None, None, "No resume link or file path provided."

    filename = format_pdf_filename(user_name)

    try:
        local_p = Path(target)
        if local_p.is_file():
            content = local_p.read_bytes()
            if len(content) > 0:
                return content, local_p.name or filename, None
    except Exception:
        pass

    if not target.startswith(("http://", "https://")):
        return None, None, f"Unsupported link or file path: {target}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    drive_id = extract_drive_id(target)
    download_urls = []
    if drive_id:
        if "docs.google.com/document" in target:
            download_urls.append(f"https://docs.google.com/document/d/{drive_id}/export?format=pdf")
        download_urls.extend([
            f"https://drive.usercontent.google.com/download?id={drive_id}&export=download&authuser=0",
            f"https://drive.google.com/uc?export=download&id={drive_id}",
        ])
    else:
        if "dropbox.com" in target and "?dl=0" in target:
            target = target.replace("?dl=0", "?dl=1")
        download_urls.append(target)

    with httpx.Client(timeout=20.0, follow_redirects=True, headers=headers) as client:
        for d_url in download_urls:
            try:
                res = client.get(d_url)
                if res.status_code == 200 and len(res.content) > 100:
                    content_type = res.headers.get("content-type", "").lower()
                    if res.content.startswith(b"%PDF") or "application/pdf" in content_type or "octet-stream" in content_type:
                        return res.content, filename, None
                    if len(res.content) > 1000 and b"<!DOCTYPE html" not in res.content[:200]:
                        return res.content, filename, None
            except Exception:
                continue

    return None, None, "Could not download a valid PDF from the provided link."
