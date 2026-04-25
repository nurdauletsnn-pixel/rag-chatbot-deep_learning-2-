import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time

BASE_URL = "https://fastapi.tiangolo.com"

URLS = [
    "/", "/tutorial/", "/tutorial/first-steps/", "/tutorial/path-params/",
    "/tutorial/query-params/", "/tutorial/body/", "/tutorial/query-params-str-validations/",
    "/tutorial/path-params-numeric-validations/", "/tutorial/body-multiple-params/",
    "/tutorial/body-fields/", "/tutorial/body-nested-models/", "/tutorial/schema-extra-example/",
    "/tutorial/extra-data-types/", "/tutorial/cookie-params/", "/tutorial/header-params/",
    "/tutorial/response-model/", "/tutorial/extra-models/", "/tutorial/response-status-code/",
    "/tutorial/request-forms/", "/tutorial/request-files/", "/tutorial/request-forms-and-files/",
    "/tutorial/handling-errors/", "/tutorial/path-operation-configuration/",
    "/tutorial/encoder/", "/tutorial/body-updates/", "/tutorial/dependencies/",
    "/tutorial/dependencies/classes-as-dependencies/", "/tutorial/dependencies/sub-dependencies/",
    "/tutorial/dependencies/dependencies-in-path-operation-decorators/",
    "/tutorial/dependencies/global-dependencies/", "/tutorial/dependencies/dependencies-with-yield/",
    "/tutorial/security/", "/tutorial/security/oauth2-jwt/", "/tutorial/middleware/",
    "/tutorial/cors/", "/tutorial/sql-databases/", "/tutorial/bigger-applications/",
    "/tutorial/background-tasks/", "/tutorial/metadata/", "/tutorial/static-files/",
    "/tutorial/testing/", "/tutorial/debugging/",
    "/advanced/", "/advanced/path-operation-advanced-configuration/",
    "/advanced/additional-status-codes/", "/advanced/response-directly/",
    "/advanced/custom-response/", "/advanced/websockets/",
    "/deployment/", "/deployment/versions/", "/deployment/https/", "/deployment/docker/",
    "/deployment/manually/", "/deployment/server-workers/", "/deployment/https/",
    "/features/", "/help-fastapi/", "/contributing/", "/news/", "/newsletter/",
    "/project-generator/", "/fastapi-people/", "/about/", "/alternatives/",
    "/history-design/", "/benchmarks/", "/external-links/"
]

def scrape() -> None:
    """Scrape FastAPI documentation pages and save as HTML files."""
    out_dir = Path("data/raw/html")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    headers = {"User-Agent": "Mozilla/5.0 (RAG project scraper)"}
    
    for path in URLS:
        url = BASE_URL + path
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                fname = path.strip("/").replace("/", "_") or "index"
                fpath = out_dir / f"{fname}.html"
                fpath.write_text(response.text, encoding="utf-8")
                print(f"✓ {path}")
            else:
                print(f"✗ {path} → {response.status_code}")
            time.sleep(0.3)  # Respect rate limits
        except Exception as e:
            print(f"✗ {path} → {e}")

if __name__ == "__main__":
    scrape()