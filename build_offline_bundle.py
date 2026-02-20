#!/usr/bin/env python3
import hashlib
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
if SCRIPT_DIR.name == "offline_content":
    ROOT = SCRIPT_DIR.parent
    OFFLINE_DIR = SCRIPT_DIR
else:
    ROOT = SCRIPT_DIR
    OFFLINE_DIR = ROOT / "offline_content"

EXERCISES_DIR = ROOT / "exercises"
ASSETS_DIR = OFFLINE_DIR / "assets"

ALLOWED_DOMAINS = {"automatetheboringstuff.com", "inventwithpython.com"}


CHAPTERS = [
    (1, "python_basics"),
    (2, "if_else_and_flow_control"),
    (3, "loops"),
    (4, "functions"),
    (5, "debugging"),
    (6, "lists"),
    (7, "dictionaries_and_structuring_data"),
    (8, "strings_and_text_editing"),
    (9, "text_pattern_matching_with_regular_expressions"),
    (10, "reading_and_writing_files"),
    (11, "organizing_files"),
    (12, "designing_and_deploying_command_line_programs"),
    (13, "web_scraping"),
    (14, "excel_spreadsheets"),
    (15, "google_sheets"),
    (16, "sqlite_databases"),
    (17, "pdf_and_word_documents"),
    (18, "csv_json_and_xml_files"),
    (19, "keeping_time_scheduling_tasks_and_launching_programs"),
    (20, "sending_email_texts_and_push_notifications"),
    (21, "making_graphs_and_manipulating_images"),
    (22, "recognizing_text_in_images"),
    (23, "controlling_the_keyboard_and_mouse"),
    (24, "text_to_speech_and_speech_recognition_engines"),
]


BOOK_PAGES = [
    (
        "Introduction",
        "https://automatetheboringstuff.com/3e/chapter0.html",
        "book/chapter0.html",
    )
]
BOOK_PAGES.extend(
    (
        f"Chapter {n}",
        f"https://automatetheboringstuff.com/3e/chapter{n}.html",
        f"book/chapter{n}.html",
    )
    for n, _ in CHAPTERS
)
BOOK_PAGES.extend(
    [
        (
            "Appendix A",
            "https://automatetheboringstuff.com/3e/appendixa.html",
            "book/appendixa.html",
        ),
        (
            "Appendix B",
            "https://automatetheboringstuff.com/3e/appendixb.html",
            "book/appendixb.html",
        ),
    ]
)

WORKBOOK_PAGES = [
    (
        "Introduction",
        "https://inventwithpython.com/automate3workbook/introduction.html",
        "workbook/introduction.html",
    )
]
WORKBOOK_PAGES.extend(
    (
        f"Chapter {n}",
        f"https://inventwithpython.com/automate3workbook/chapter{n}.html",
        f"workbook/chapter{n}.html",
    )
    for n, _ in CHAPTERS
)
WORKBOOK_PAGES.append(
    (
        "Answers",
        "https://inventwithpython.com/automate3workbook/answers.html",
        "workbook/answers.html",
    )
)

ALL_PAGES = BOOK_PAGES + WORKBOOK_PAGES
PAGE_MAP = {url: local for _, url, local in ALL_PAGES}


def build_navigation_order():
    ordered = [
        ("Book Introduction", "book/chapter0.html"),
        ("Workbook Introduction", "workbook/introduction.html"),
    ]
    for n, _ in CHAPTERS:
        ordered.append((f"Book Chapter {n}", f"book/chapter{n}.html"))
        ordered.append((f"Workbook Chapter {n}", f"workbook/chapter{n}.html"))
    ordered.extend(
        [
            ("Book Appendix A", "book/appendixa.html"),
            ("Book Appendix B", "book/appendixb.html"),
            ("Workbook Answers", "workbook/answers.html"),
        ]
    )
    return ordered


NAV_ORDER = build_navigation_order()
NAV_INDEX = {path: idx for idx, (_, path) in enumerate(NAV_ORDER)}
NAV_LABEL = {path: label for label, path in NAV_ORDER}


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    clean = parsed._replace(fragment="")
    return urlunparse(clean)


def is_http(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def should_handle_url(url: str) -> bool:
    if not is_http(url):
        return False
    host = (urlparse(url).hostname or "").lower()
    return host in ALLOWED_DOMAINS


def path_for_asset(url: str) -> Path:
    parsed = urlparse(url)
    host = parsed.hostname or "unknown"
    raw_path = parsed.path or "/"
    if raw_path.endswith("/"):
        raw_path += "index"
    ext = Path(raw_path).suffix
    if not ext:
        raw_path += ".bin"
    local = ASSETS_DIR / host / raw_path.lstrip("/")
    if parsed.query:
        qhash = hashlib.sha1(parsed.query.encode("utf-8")).hexdigest()[:10]
        local = local.with_name(f"{local.stem}__q_{qhash}{local.suffix}")
    return local


def relative_link(from_file: Path, to_file: Path) -> str:
    return os.path.relpath(to_file, from_file.parent).replace("\\", "/")


downloaded_assets = {}


def fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (offline-bundle-builder)"})
    with urlopen(req, timeout=30) as resp:
        return resp.read()


def rewrite_css_urls(css_text: str, base_url: str, css_file: Path) -> str:
    def repl_url(match):
        inner = match.group(1).strip().strip("\"'")
        if not inner or inner.startswith("data:"):
            return f"url({match.group(1)})"
        full = normalize_url(urljoin(base_url, inner))
        if should_handle_url(full):
            try:
                target = download_asset(full)
                rel = relative_link(css_file, target)
                return f"url('{rel}')"
            except Exception:
                return f"url({match.group(1)})"
        return f"url({match.group(1)})"

    def repl_import(match):
        q = match.group(1).strip("\"'")
        full = normalize_url(urljoin(base_url, q))
        if should_handle_url(full):
            try:
                target = download_asset(full)
                rel = relative_link(css_file, target)
                return f"@import url('{rel}')"
            except Exception:
                return match.group(0)
        return match.group(0)

    css_text = re.sub(r"url\(([^)]+)\)", repl_url, css_text)
    css_text = re.sub(r"@import\s+url\(([^)]+)\)", repl_import, css_text)
    return css_text


def download_asset(url: str) -> Path:
    url = normalize_url(url)
    if url in downloaded_assets:
        return downloaded_assets[url]

    local = path_for_asset(url)
    local.parent.mkdir(parents=True, exist_ok=True)
    data = fetch_bytes(url)

    if local.suffix.lower() == ".css":
        try:
            css_text = data.decode("utf-8")
        except UnicodeDecodeError:
            css_text = data.decode("latin-1")
        css_text = rewrite_css_urls(css_text, url, local)
        local.write_text(css_text, encoding="utf-8")
    else:
        local.write_bytes(data)

    downloaded_assets[url] = local
    return local


ATTR_RE = re.compile(
    r"(?P<attr>\b(?:href|src|poster)=)(?P<quote>[\"'])(?P<url>.*?)(?P=quote)",
    re.IGNORECASE,
)
SRCSET_RE = re.compile(
    r"\bsrcset=(?P<quote>[\"'])(?P<value>.*?)(?P=quote)", re.IGNORECASE | re.DOTALL
)
STYLE_URL_RE = re.compile(r"url\((?P<inner>[^)]+)\)", re.IGNORECASE)


def is_probable_asset(full_url: str, attr_name: str) -> bool:
    attr_name = attr_name.lower()
    if attr_name.startswith("src") or "poster" in attr_name:
        return True
    path = (urlparse(full_url).path or "").lower()
    exts = (
        ".css",
        ".js",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".svg",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".eot",
        ".mp4",
        ".webm",
        ".mp3",
        ".pdf",
        ".zip",
    )
    return path.endswith(exts)


def rewrite_html_urls(html_text: str, page_url: str, local_path: Path) -> str:
    def replace_attr(match):
        attr = match.group("attr")
        quote = match.group("quote")
        raw = match.group("url")
        if raw.startswith(("mailto:", "javascript:", "tel:", "#", "data:")):
            return match.group(0)

        fragment = ""
        if "#" in raw:
            raw, frag = raw.split("#", 1)
            fragment = f"#{frag}"

        full = normalize_url(urljoin(page_url, raw))

        if full in PAGE_MAP:
            target = OFFLINE_DIR / PAGE_MAP[full]
            rel = relative_link(local_path, target)
            return f"{attr}{quote}{rel}{fragment}{quote}"

        if should_handle_url(full) and is_probable_asset(full, attr):
            try:
                target = download_asset(full)
                rel = relative_link(local_path, target)
                return f"{attr}{quote}{rel}{fragment}{quote}"
            except Exception:
                return match.group(0)

        return match.group(0)

    def replace_srcset(match):
        value = match.group("value")
        quote = match.group("quote")
        parts = []
        for chunk in value.split(","):
            item = chunk.strip()
            if not item:
                continue
            bits = item.split()
            raw_url = bits[0]
            descriptor = " ".join(bits[1:])
            full = normalize_url(urljoin(page_url, raw_url))
            if should_handle_url(full):
                try:
                    target = download_asset(full)
                    rel = relative_link(local_path, target)
                    item = f"{rel} {descriptor}".strip()
                except Exception:
                    item = chunk.strip()
            parts.append(item)
        return f"srcset={quote}{', '.join(parts)}{quote}"

    def replace_style_url(match):
        inner = match.group("inner").strip().strip("\"'")
        if not inner or inner.startswith("data:"):
            return match.group(0)
        full = normalize_url(urljoin(page_url, inner))
        if should_handle_url(full):
            try:
                target = download_asset(full)
                rel = relative_link(local_path, target)
                return f"url('{rel}')"
            except Exception:
                return match.group(0)
        return match.group(0)

    html_text = ATTR_RE.sub(replace_attr, html_text)
    html_text = SRCSET_RE.sub(replace_srcset, html_text)
    html_text = STYLE_URL_RE.sub(replace_style_url, html_text)
    return html_text


def add_page_navigation(html_text: str, local_rel: str, local_path: Path) -> str:
    idx = NAV_INDEX.get(local_rel)
    if idx is None:
        return html_text

    prev_href = ""
    prev_label = ""
    if idx > 0:
        prev_path = OFFLINE_DIR / NAV_ORDER[idx - 1][1]
        prev_href = relative_link(local_path, prev_path)
        prev_label = NAV_ORDER[idx - 1][0]

    next_href = ""
    next_label = ""
    if idx < len(NAV_ORDER) - 1:
        next_path = OFFLINE_DIR / NAV_ORDER[idx + 1][1]
        next_href = relative_link(local_path, next_path)
        next_label = NAV_ORDER[idx + 1][0]

    home_href = relative_link(local_path, OFFLINE_DIR / "index.html")
    current = NAV_LABEL[local_rel]

    prev_node = (
        f"<a class='atbs-nav-link' href='{prev_href}' aria-label='Previous chapter'>&larr; {prev_label}</a>"
        if prev_href
        else "<span class='atbs-nav-link atbs-nav-disabled'>&larr; Start</span>"
    )
    next_node = (
        f"<a class='atbs-nav-link' href='{next_href}' aria-label='Next chapter'>{next_label} &rarr;</a>"
        if next_href
        else "<span class='atbs-nav-link atbs-nav-disabled'>End &rarr;</span>"
    )

    nav_block = (
        "<style>"
        ".atbs-nav{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;justify-content:space-between;"
        "margin:1rem 0;padding:.7rem .8rem;border:1px solid #cfd8dc;border-radius:10px;background:#f6fbfd;font:14px/1.35 system-ui,-apple-system,sans-serif;}"
        ".atbs-nav-center{color:#455a64;font-weight:600;}"
        ".atbs-nav-link{text-decoration:none;color:#0b5b6b;background:#e6f3f7;border:1px solid #c7dfe7;border-radius:7px;padding:.42rem .55rem;display:inline-block;}"
        ".atbs-nav-link:hover{background:#d9edf3;}"
        ".atbs-nav-disabled{opacity:.55;cursor:not-allowed;}"
        "</style>"
        "<nav class='atbs-nav' aria-label='Chapter pagination'>"
        f"{prev_node}"
        f"<span class='atbs-nav-center'><a class='atbs-nav-link' href='{home_href}'>Contents</a> {current}</span>"
        f"{next_node}"
        "</nav>"
    )

    body_open = re.search(r"<body[^>]*>", html_text, flags=re.IGNORECASE)
    if body_open:
        insert_at = body_open.end()
        html_text = html_text[:insert_at] + nav_block + html_text[insert_at:]

    html_text = re.sub(
        r"</body>", nav_block + "</body>", html_text, count=1, flags=re.IGNORECASE
    )
    return html_text


def strip_repeating_promo(html_text: str) -> str:
    # Remove the repeated closeable promo block from chapter pages.
    return re.sub(
        r"<div[^>]*id=[\"']closeable_ad_bar\d*[\"'][^>]*>.*?</div>",
        "",
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )


def fetch_and_write_page(label: str, page_url: str, local_rel: str):
    local_path = OFFLINE_DIR / local_rel
    local_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {label}: {page_url}")
    data = fetch_bytes(page_url)
    try:
        html = data.decode("utf-8")
    except UnicodeDecodeError:
        html = data.decode("latin-1")
    html = rewrite_html_urls(html, page_url, local_path)
    html = strip_repeating_promo(html)
    html = add_page_navigation(html, local_rel, local_path)
    local_path.write_text(html, encoding="utf-8")


def write_index():
    lines = [
        "<!doctype html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='utf-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1'>",
        "  <title>Automate the Boring Stuff Offline</title>",
        "  <style>",
        "    :root { --bg:#f6f5ef; --panel:#fffdf7; --ink:#1e2430; --muted:#5d6472; --line:#ddd4c6; --accent:#0e7a6d; }",
        "    body{margin:0;padding:2rem;font:16px/1.45 Georgia, 'Times New Roman', serif;background:linear-gradient(180deg,#f8f5ec,#eef3f5);color:var(--ink);}",
        "    .wrap{max-width:920px;margin:0 auto;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1.5rem 1.25rem;box-shadow:0 12px 28px rgba(0,0,0,.06);}",
        "    h1{margin:.2rem 0 .4rem;font-size:1.6rem;text-align:center;}",
        "    p{color:var(--muted);margin:.2rem 0 1rem;text-align:center;}",
        "    .offline-text{display:inline-block;background:linear-gradient(90deg,#0b6d62,#129488,#0b6d62);background-size:200% auto;color:transparent;-webkit-background-clip:text;background-clip:text;text-shadow:0 0 12px rgba(18,148,136,.24);animation:offlineWave 3.6s linear infinite;}",
        "    @keyframes offlineWave{0%{background-position:0% 50%}100%{background-position:200% 50%}}",
        "    h2{margin:1.2rem 0 .6rem;font-size:1.15rem;border-top:1px solid var(--line);padding-top:.9rem;}",
        "    ul{list-style:none;padding:0;margin:0;display:grid;gap:.5rem;}",
        "    li{display:grid;grid-template-columns:1fr 1fr;gap:.6rem;padding:.55rem;border:1px solid #ebe4d8;border-radius:10px;background:#fffcf6;}",
        "    a{display:block;text-decoration:none;padding:.48rem .58rem;border-radius:8px;background:#f2fbf8;color:#075449;border:1px solid #cde6df;}",
        "    a:hover{background:#e6f6f2;}",
        "    .ref{display:flex;flex-wrap:wrap;gap:.55rem;}",
        "    .promo{margin-top:.9rem;padding:.85rem;border:1px solid #e1dbce;border-radius:10px;background:#fefaf1;}",
        "    .promo p{margin:.35rem 0 .5rem;}",
        "    .promo-links{display:flex;flex-wrap:wrap;gap:.5rem;}",
        "    @media (max-width:740px){body{padding:1rem}li{grid-template-columns:1fr}}",
        "  </style>",
        "</head>",
        "<body>",
        "  <main class='wrap'>",
        "    <h1>Automate the Boring Stuff <span class='offline-text'>Offline</span></h1>",
        "    <p>Read each main-book chapter, then jump directly to the matching workbook chapter.</p>",
        "    <h2>Introductions</h2>",
        "    <ul>",
        "      <li><a href='book/chapter0.html'>Book Introduction</a><a href='workbook/introduction.html'>Workbook Introduction</a></li>",
        "    </ul>",
        "    <h2>Chapter Pairs</h2>",
        "    <ul>",
    ]

    for n, slug in CHAPTERS:
        lines.append(
            f"      <li><a href='book/chapter{n}.html'>Book Chapter {n}</a><a href='workbook/chapter{n}.html'>Workbook Chapter {n}</a></li>"
        )

    lines.extend(
        [
            "    </ul>",
            "    <h2>Reference</h2>",
            "    <div class='ref'>",
            "      <a href='book/appendixa.html'>Book Appendix A</a>",
            "      <a href='book/appendixb.html'>Book Appendix B</a>",
            "      <a href='workbook/answers.html'>Workbook Answers</a>",
            "    </div>",
            "    <div class='promo'>",
            "      <p><strong>More from Al Sweigart</strong>:</p>",
            "      <div class='promo-links'>",
            "        <a href='https://inventwithpython.com'>Free online books hub</a>",
            "        <a href='https://nostarch.com/automate-boring-stuff-python-3rd-edition'>Automate book page</a>",
            "        <a href='https://inventwithpython.com/automateudemy'>Automate video course</a>",
            "      </div>",
            "    </div>",
            "  </main>",
            "</body>",
            "</html>",
        ]
    )

    (OFFLINE_DIR / "index.html").write_text("\n".join(lines), encoding="utf-8")


def write_exercises():
    EXERCISES_DIR.mkdir(parents=True, exist_ok=True)
    intro = EXERCISES_DIR / "00_intro"
    intro.mkdir(exist_ok=True)
    intro_readme = """# Intro Setup Checklist

Use this folder to test your baseline setup flow before chapter 1.

## Manual repetition checklist

1. Create a virtual environment: `python3 -m venv .venv`
2. Activate it: `source .venv/bin/activate`
3. Upgrade pip: `python -m pip install -U pip`
4. Create your own practice file(s) and run them.
"""
    (intro / "README.md").write_text(intro_readme, encoding="utf-8")

    for n, slug in CHAPTERS:
        chapter_dir = EXERCISES_DIR / f"{n:02d}_{slug}"
        chapter_dir.mkdir(exist_ok=True)
        text = f"""# Chapter {n} Exercise Workspace

Mirror workflow: complete this chapter in `offline_content/index.html`, then practice here.

## Project initialization (manual muscle memory)

1. `python3 -m venv .venv`
2. `source .venv/bin/activate`
3. `python -m pip install -U pip`
4. Create files/folders yourself for this chapter (`src`, `tests`, scripts, notes).
5. Run your code and iterate.

Keep this folder lightweight so you can re-initialize from scratch when needed.
"""
        (chapter_dir / "README.md").write_text(text, encoding="utf-8")


def main():
    OFFLINE_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    for label, page_url, local_rel in ALL_PAGES:
        fetch_and_write_page(label, page_url, local_rel)

    write_index()
    write_exercises()
    print("Done. Open offline_content/index.html in your browser.")


if __name__ == "__main__":
    main()
