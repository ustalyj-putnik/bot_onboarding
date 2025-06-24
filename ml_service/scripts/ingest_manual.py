import re, html, argparse
from bs4 import BeautifulSoup
from pathlib import Path

HTML_TAG_RE = re.compile(r"<[^>]+>", flags=re.MULTILINE)

def extract_text(html_str: str) -> str:
    soup = BeautifulSoup(html_str, "lxml")
    # Удаляем скрипты/стили
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    return html.unescape(text)

def main(src_dir: Path):
    dest_dir = Path("ml_service/data_ingest/raw/manual")
    dest_dir.mkdir(parents=True, exist_ok=True)

    for html_file in src_dir.glob("*.html"):
        txt = extract_text(html_file.read_text(encoding="utf-8"))
        dest = dest_dir / f"{html_file.stem}.txt"
        dest.write_text(txt, encoding="utf-8")
        print("✔", html_file.name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src", help="папка с .html")
    args = parser.parse_args()
    main(Path(args.src))