"""Read-only smoke checks for the public Pages deployment (stdlib only)."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import html
import json
from pathlib import Path
import re
import time
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://bakapiano.github.io/")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    site = Path(__file__).resolve().parents[1]
    manifest = json.loads((site / "migration/report.json").read_text(encoding="utf-8"))
    jobs = [("/", "home", ""), ("/legacy-blog/", "archive", "")]
    for article in manifest["articles"]:
        jobs.append((article["new_path"], "article", article["title"]))
        jobs.append((article["old_path"], "alias", article["new_path"]))
    for image in manifest["images"]:
        if image.get("local"):
            jobs.append((image["local"], "asset", ""))
    jobs.extend([
        ("/vendor/mathjax/tex-chtml.js", "asset", ""),
        ("/vendor/mathjax/output/chtml/fonts/woff-v2/MathJax_Main-Regular.woff", "asset", ""),
        ("/llms.txt", "asset", ""),
    ])

    def check(job):
        path, kind, expected = job
        for attempt in range(3):
            try:
                req = Request(base + quote(path, safe="/"), headers={
                    "User-Agent": "Bakapiano-Pages-Smoke-Test",
                    "Cache-Control": "no-cache",
                })
                with urlopen(req, timeout=20) as response:
                    body = response.read()
                    assert response.status == 200, f"HTTP {response.status}"
                    assert body, "Empty response"
                if kind != "asset":
                    text = body.decode("utf-8")
                    if kind == "home":
                        assert "记录、整理" in text and "legacy-blog" in text, "Old or unexpected homepage"
                    elif kind == "archive":
                        assert "旧博客（算法竞赛）" in text and "22 篇文章" in text, "Archive not deployed"
                    elif kind == "article":
                        title = re.search(r"<title>(.*?)</title>", text, re.S)
                        assert title and expected in html.unescape(title.group(1)), "Wrong article title"
                        assert "kb-post-meta" in text, "Article template missing"
                    elif kind == "alias":
                        assert re.search(r"http-equiv=[\"']?refresh", text, re.I), "Missing legacy redirect"
                        assert expected in unquote(text), "Incorrect legacy redirect destination"
                return {"path": path, "kind": kind, "ok": True}
            except Exception as exc:
                if attempt < 2:
                    time.sleep(5)
                else:
                    return {"path": path, "kind": kind, "ok": False, "error": str(exc)}

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(check, jobs))
    failures = [r for r in results if not r["ok"]]
    print(json.dumps({"base_url": base, "checked": len(results),
                      "passed": len(results) - len(failures), "failures": failures},
                     ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
