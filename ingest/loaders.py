from pathlib import Path
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import List, Optional
import re

@dataclass
class Document:
    """Unified document object with content and metadata."""
    page_content: str
    metadata: dict = field(default_factory=dict)


def normalize_source_id(source: str) -> str:
    """Create a stable citation-safe identifier from a URL or local source."""
    source = source.strip()
    source = re.sub(r"^https?://fastapi\.tiangolo\.com/?", "", source)
    source = re.sub(r"^github://tiangolo/fastapi/?", "github/", source)
    source = source.strip("/")
    source = re.sub(r"\.(html|md)$", "", source)
    source = source.replace("_", "/")
    source = re.sub(r"[^A-Za-z0-9/_-]+", "-", source)
    source = re.sub(r"-{2,}", "-", source).strip("-/")
    return source or "index"


def _extract_html_date(soup: BeautifulSoup) -> Optional[str]:
    """Extract publication/update date when present in the HTML metadata."""
    selectors = [
        ("meta", {"property": "article:modified_time"}),
        ("meta", {"property": "article:published_time"}),
        ("meta", {"name": "date"}),
        ("meta", {"name": "lastmod"}),
        ("meta", {"name": "revision"}),
    ]
    for tag_name, attrs in selectors:
        tag = soup.find(tag_name, attrs=attrs)
        if tag and tag.get("content"):
            return tag["content"].strip()

    time_tag = soup.find("time")
    if time_tag:
        return (time_tag.get("datetime") or time_tag.get_text(strip=True) or None)
    return None


def _extract_markdown_date(content: str) -> Optional[str]:
    """Extract a simple YAML-frontmatter date field when present."""
    if not content.startswith("---"):
        return None
    end = content.find("\n---", 3)
    if end == -1:
        return None
    frontmatter = content[3:end]
    for line in frontmatter.splitlines():
        if line.lower().startswith("date:"):
            return line.split(":", 1)[1].strip().strip('"\'') or None
    return None


def _metadata(source: str, title: str, filename: str, doc_type: str, date: Optional[str]) -> dict:
    """Build metadata that survives chunking, indexing, retrieval, and citations.

    Chroma does not accept Python None metadata values, so unavailable dates are
    stored as the literal string "None" and documented in the report/README.
    """
    source_id = normalize_source_id(source)
    return {
        "source": source,
        "source_id": source_id,
        "citation_id": source_id,
        "title": title,
        "filename": filename,
        "doc_type": doc_type,
        "date": date or "None",
    }

def load_html(html_dir: str = "data/raw/html") -> List[Document]:
    """Load HTML documents, extract content and metadata."""
    docs = []
    for fpath in Path(html_dir).glob("*.html"):
        text = fpath.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(text, "html.parser")
        
        # Extract title
        title_tag = soup.find("h1") or soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else fpath.stem
        canonical = soup.find("link", rel="canonical")
        source = canonical.get("href").rstrip("/") if canonical and canonical.get("href") else (
            f"https://fastapi.tiangolo.com/{fpath.stem.replace('_', '/')}"
        )
        date = _extract_html_date(soup)
        
        # Remove nav, footer, scripts
        for tag in soup(["nav", "footer", "script", "style", "header"]):
            tag.decompose()
        
        # Get main content
        main = soup.find("article") or soup.find("main") or soup.find("body")
        content = main.get_text(separator="\n", strip=True) if main else ""
        content = re.sub(r'\n{3,}', '\n\n', content)  # Clean whitespace
        
        if len(content) > 100:
            docs.append(Document(
                page_content=content,
                metadata=_metadata(source, title, fpath.name, "html", date)
            ))
    print(f"Loaded {len(docs)} HTML documents")
    return docs

def load_markdown(md_dir: str = "data/raw/markdown") -> List[Document]:
    """Load Markdown documents, extract content and metadata."""
    docs = []
    for fpath in Path(md_dir).glob("**/*.md"):
        content = fpath.read_text(encoding="utf-8", errors="ignore")
        
        # Extract title from first # heading
        title = fpath.stem
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Create GitHub source URL
        relative_path = fpath.relative_to(md_dir)
        source = f"https://github.com/fastapi/fastapi/blob/master/docs/en/docs/{relative_path}"
        
        date = _extract_markdown_date(content)
        
        if len(content) > 100:
            docs.append(Document(
                page_content=content,
                metadata=_metadata(source, title, str(relative_path), "markdown", date)
            ))
    print(f"Loaded {len(docs)} Markdown documents")
    return docs

def load_all() -> List[Document]:
    """Load all documents from HTML and Markdown directories."""
    return load_html() + load_markdown()
