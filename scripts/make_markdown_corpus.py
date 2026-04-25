import argparse
from pathlib import Path
import re

from bs4 import BeautifulSoup


DEFAULT_HTML_FILES = [
    "index.html",
    "tutorial_first-steps.html",
    "tutorial_path-params.html",
    "tutorial_query-params.html",
    "tutorial_body.html",
    "tutorial_dependencies.html",
    "tutorial_cors.html",
    "tutorial_request-files.html",
    "tutorial_middleware.html",
    "tutorial_testing.html",
    "tutorial_security.html",
    "tutorial_response-model.html",
]


def _clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def html_to_markdown(html_path: Path) -> str:
    """Create a lightweight Markdown document from a locally scraped FastAPI page."""
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    for tag in soup(["nav", "footer", "script", "style", "header"]):
        tag.decompose()

    title_tag = soup.find("h1") or soup.find("title")
    title = title_tag.get_text(strip=True).replace("¶", "") if title_tag else html_path.stem
    canonical = soup.find("link", rel="canonical")
    source = canonical.get("href").rstrip("/") if canonical and canonical.get("href") else (
        f"https://fastapi.tiangolo.com/{html_path.stem.replace('_', '/')}"
    )
    main = soup.find("article") or soup.find("main") or soup.find("body")
    body = _clean_text(main.get_text(separator="\n", strip=True) if main else "")
    return f"---\nsource: {source}\ndate: None\n---\n\n# {title}\n\n{body}\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Markdown corpus from local FastAPI HTML pages.")
    parser.add_argument("--html-dir", default="data/raw/html")
    parser.add_argument("--out-dir", default="data/raw/markdown")
    parser.add_argument("--all", action="store_true", help="Convert every local HTML page instead of a focused subset.")
    args = parser.parse_args()

    html_dir = Path(args.html_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    html_files = sorted(html_dir.glob("*.html")) if args.all else [html_dir / name for name in DEFAULT_HTML_FILES]
    written = 0
    for html_path in html_files:
        if not html_path.exists():
            continue
        md_name = html_path.with_suffix(".md").name
        (out_dir / md_name).write_text(html_to_markdown(html_path), encoding="utf-8")
        written += 1

    print(f"Wrote {written} Markdown files to {out_dir}")


if __name__ == "__main__":
    main()
