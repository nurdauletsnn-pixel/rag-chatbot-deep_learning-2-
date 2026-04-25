import requests
from pathlib import Path
import time

BASE_URL = "https://raw.githubusercontent.com/fastapi/fastapi/master/docs/en/docs"

# List of markdown file paths in the FastAPI docs
MARKDOWN_PATHS = [
    "index.md",
    "tutorial/index.md",
    "tutorial/first-steps.md",
    "tutorial/path-params.md",
    "tutorial/query-params.md",
    "tutorial/body.md",
    "tutorial/query-params-str-validations.md",
    "tutorial/path-params-numeric-validations.md",
    "tutorial/body-multiple-params.md",
    "tutorial/body-fields.md",
    "tutorial/body-nested-models.md",
    "tutorial/schema-extra-example.md",
    "tutorial/extra-data-types.md",
    "tutorial/cookie-params.md",
    "tutorial/header-params.md",
    "tutorial/response-model.md",
    "tutorial/extra-models.md",
    "tutorial/response-status-code.md",
    "tutorial/request-forms.md",
    "tutorial/request-files.md",
    "tutorial/request-forms-and-files.md",
    "tutorial/handling-errors.md",
    "tutorial/path-operation-configuration.md",
    "tutorial/encoder.md",
    "tutorial/body-updates.md",
    "tutorial/dependencies/index.md",
    "tutorial/dependencies/classes-as-dependencies.md",
    "tutorial/dependencies/sub-dependencies.md",
    "tutorial/dependencies/dependencies-in-path-operation-decorators.md",
    "tutorial/dependencies/global-dependencies.md",
    "tutorial/dependencies/dependencies-with-yield.md",
    "tutorial/security/index.md",
    "tutorial/security/oauth2-jwt.md",
    "tutorial/middleware.md",
    "tutorial/cors.md",
    "tutorial/sql-databases.md",
    "tutorial/bigger-applications.md",
    "tutorial/background-tasks.md",
    "tutorial/metadata.md",
    "tutorial/static-files.md",
    "tutorial/testing.md",
    "tutorial/debugging.md",
    "advanced/index.md",
    "advanced/path-operation-advanced-configuration.md",
    "advanced/additional-status-codes.md",
    "advanced/response-directly.md",
    "advanced/custom-response.md",
    "advanced/websockets.md",
    "deployment/index.md",
    "deployment/versions.md",
    "deployment/https.md",
    "deployment/docker.md",
    "deployment/manually.md",
    "deployment/server-workers.md",
    "features.md",
    "help-fastapi.md",
    "contributing.md",
    "news.md",
    "newsletter.md",
    "project-generator.md",
    "fastapi-people.md",
    "about.md",
    "alternatives.md",
    "history-design.md",
    "benchmarks.md",
    "external-links.md"
]

def download_markdown() -> None:
    """Download FastAPI documentation markdown files from GitHub."""
    out_dir = Path("data/raw/markdown")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    headers = {"User-Agent": "Mozilla/5.0 (RAG project downloader)"}
    
    for path in MARKDOWN_PATHS:
        url = f"{BASE_URL}/{path}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Create subdirectories if needed
                file_path = out_dir / path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_path.write_text(response.text, encoding="utf-8")
                print(f"✓ Downloaded {path}")
                time.sleep(0.1)  # Be nice to GitHub
            else:
                print(f"✗ Failed to download {path} (status: {response.status_code})")
        except Exception as e:
            print(f"✗ Error downloading {path}: {e}")

if __name__ == "__main__":
    download_markdown()