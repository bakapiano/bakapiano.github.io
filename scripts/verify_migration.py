"""Verify built pages against the migration manifest. Run after hugo build."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from bs4 import BeautifulSoup
import yaml


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public", type=Path, default=Path("public"))
    parser.add_argument("--base-path", default="/")
    args = parser.parse_args()
    site = Path(__file__).resolve().parents[1]
    public = args.public.resolve()
    report = json.loads((site / "migration/report.json").read_text(encoding="utf-8"))
    failures = []
    totals = Counter()
    parsed_pages = {}

    def parse_page(path):
        if path not in parsed_pages:
            parsed_pages[path] = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        return parsed_pages[path]

    def check(ok, message):
        if not ok:
            failures.append(message)

    def output_path(path):
        decoded = unquote(path)
        prefix = args.base_path.rstrip("/")
        if prefix:
            if not (decoded == prefix or decoded.startswith(prefix + "/")):
                return None
            decoded = decoded[len(prefix):]
        target = public / decoded.lstrip("/")
        if target.is_dir() or decoded.endswith("/"):
            target /= "index.html"
        return target

    check(len(report["articles"]) == 22, "Expected 22 articles")
    for entry in report["articles"]:
        title = entry["title"]
        md = (site / entry["markdown"]).read_text(encoding="utf-8")
        front = yaml.safe_load(md.split("---", 2)[1])
        check(front["title"] == title, f"Title changed: {title}")
        check(front["date"] == entry["date"], f"Date changed: {title}")
        check(front["categories"] == ["旧博客（算法竞赛）"], f"Wrong category: {title}")
        check("MIGRATIONTOKEN" not in md, f"Unrestored token: {title}")
        path = public / entry["new_path"].lstrip("/") / "index.html"
        check(path.exists(), f"Missing article: {path}")
        if not path.exists():
            continue
        soup = parse_page(path)
        main = soup.select_one("main .content")
        check(main is not None, f"No article body: {title}")
        if main is None:
            continue
        codes = [sha(code.get_text().rstrip("\n")) for code in main.select("pre code")]
        expected = [c["sha256"] for c in entry["code_blocks"]]
        check(Counter(codes) == Counter(expected), f"Code block content mismatch: {title}")
        totals["code_blocks"] += len(codes)
        for heading_id in entry["heading_ids"]:
            if heading_id:
                check(main.find(id=heading_id) is not None, f"Lost heading #{heading_id}: {title}")
        for image in main.find_all("img", src=True):
            parsed = urlsplit(image["src"])
            check(not parsed.scheme, f"Image still depends on external host: {title}: {image['src']}")
            if not parsed.scheme:
                image_path = output_path(parsed.path)
                check(image_path is not None and image_path.is_file(), f"Missing image: {image['src']}")
            totals["images"] += 1
        # Audit in-body local article links and fragments, not third-party URLs.
        page_url = "https://bakapiano.github.io" + args.base_path.rstrip("/") + entry["new_path"]
        for link in main.find_all("a", href=True):
            parsed = urlsplit(urljoin(page_url, link["href"]))
            if parsed.hostname != "bakapiano.github.io":
                continue
            target = output_path(parsed.path)
            check(target is not None and target.exists(), f"Broken internal link in {title}: {link['href']}")
            if target and target.exists() and parsed.fragment and target.suffix == ".html":
                linked = parse_page(target)
                # Aliases forward to a different document; fragment resolves there.
                if not linked.select_one('meta[http-equiv="refresh"]'):
                    check(linked.find(id=unquote(parsed.fragment)) is not None,
                          f"Broken internal fragment in {title}: {link['href']}")
        alias = public / entry["old_path"].lstrip("/") / "index.html"
        check(alias.exists(), f"Missing legacy URL: {entry['old_path']}")
        if alias.exists():
            old = BeautifulSoup(alias.read_text(encoding="utf-8"), "html.parser")
            canonical = old.select_one('link[rel="canonical"]')
            check(canonical is not None and unquote(urlsplit(canonical.get("href", "")).path) == args.base_path.rstrip("/") + entry["new_path"], f"Incorrect redirect: {title}")
        totals["articles"] += 1

    archive = BeautifulSoup((public / "legacy-blog/index.html").read_text(encoding="utf-8"), "html.parser")
    check(len(archive.select(".kb-archive-list li")) == 22, "Archive must list all 22 posts")
    check((public / "llms.txt").exists(), "Missing llms.txt")
    check(all(i["status"] != "unavailable" for i in report["images"]), "Some images were not recovered")
    print(json.dumps(dict(totals=totals, failures=failures), ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)
    print("PASS: titles, dates, category, code content, heading anchors, images, local links, archive and old URLs.")


if __name__ == "__main__":
    main()
