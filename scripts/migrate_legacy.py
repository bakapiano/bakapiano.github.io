"""Recover Markdown from the public Hexo export, without modifying the source.

This is a one-time migration. Existing articles are never overwritten unless
--overwrite is explicitly supplied. Code is extracted before HTML conversion;
math and heading IDs are protected from Markdown escaping.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup, NavigableString
from markdownify import markdownify
import yaml

OLD_HOSTS = {"bakapiano.github.io", "blog.bakapiano.site", "bakapiano.site"}
CATEGORY = "旧博客（算法竞赛）"


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def convert(html_text):
    return markdownify(html_text, heading_style="ATX", bullets="-",
                       escape_underscores=True, escape_asterisks=True,
                       escape_misc=True, wrap=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--site", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    source, site = args.source.resolve(), args.site.resolve()
    articles = []
    for path in sorted(source.glob("20??/*/*/*/index.html")):
        raw_html = path.read_text(encoding="utf-8")
        duplicate_math_delimiter = "]$$，求 $k$" in raw_html
        if duplicate_math_delimiter:
            raw_html = raw_html.replace("]$$，求 $k$", "]$，求 $k$")
        tuple_repairs = re.findall(r"<([A-Za-z],[A-Za-z])>", raw_html)
        # Original Hexo treated unescaped graph edges like <S,u> as HTML tags.
        # Recover the literal notation before the HTML parser lowercases it.
        raw_html = re.sub(r"<([A-Za-z],[A-Za-z])>", lambda m: html.escape(m.group(0)), raw_html)
        soup = BeautifulSoup(raw_html, "html.parser")
        article = soup.select_one("article.article")
        if not article:
            continue
        meta = {tag.get("property"): tag.get("content") for tag in soup.select("meta[property]")}
        parts = path.relative_to(source).parts
        slug = "-".join(parts[:3]) + "-" + parts[3]
        articles.append(dict(source=path, soup=soup, article=article, meta=meta, tuple_repairs=tuple_repairs,
                             duplicate_math_delimiter=duplicate_math_delimiter,
                             slug=slug, old_path="/" + "/".join(parts[:-1]) + "/"))
    articles.sort(key=lambda a: a["meta"]["article:published_time"], reverse=True)
    if len(articles) != 22:
        raise RuntimeError(f"Expected 22 articles, found {len(articles)}; review before migration")
    mapping = {a["old_path"]: a["slug"] for a in articles}
    outputs = [site / "content/legacy-blog" / (a["slug"] + ".md") for a in articles]
    if not args.overwrite and any(path.exists() for path in outputs):
        raise SystemExit("Migrated Markdown exists. Refusing to overwrite; use --overwrite only for regeneration.")
    report = dict(source_repository="https://github.com/bakapiano/bakapiano.github.io",
                  source_commit=subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip(),
                  category=CATEGORY, articles=[], images=[], warnings=[])
    cached_images = {}
    for order, entry in enumerate(articles, 1):
        soup, content = entry["soup"], entry["article"].select_one("div.content")
        title = entry["article"].select_one("h1").get_text()
        protected = {}

        def protect(value, block=False):
            token = f"MIGRATIONTOKEN{len(protected):06d}END"
            protected[token] = value
            return NavigableString(("\n\n" if block else "") + token + ("\n\n" if block else ""))

        codes = []
        for figure in list(content.select("figure.highlight")):
            pre = figure.select_one("td.code pre")
            if pre is None:
                raise RuntimeError(f"Unrecognized code figure: {title}")
            lines = pre.select("span.line")
            code = "\n".join(line.get_text() for line in lines) if lines else pre.get_text()
            lang = next((c for c in figure.get("class", []) if c != "highlight"), "text")
            # Hexo labelled these C++ solutions as C; highlight them appropriately.
            if lang == "c":
                lang = "cpp"
            fence = "`" * max(3, max((len(x) + 1 for x in re.findall(r"`+", code)), default=3))
            codes.append(dict(sha256=sha(code.rstrip("\n")), lines=len(code.splitlines())))
            figure.replace_with(protect(f"{fence}{lang}\n{code.rstrip(chr(10))}\n{fence}", True))
        for pre in list(content.find_all("pre")):
            for br in pre.find_all("br"):
                br.replace_with("\n")
            code = pre.get_text().rstrip("\n")
            codes.append(dict(sha256=sha(code), lines=len(code.splitlines())))
            pre.replace_with(protect("```text\n" + code + "\n```", True))

        display_math = 0
        for script in list(content.find_all("script")):
            if script.get("type", "").startswith("math/tex"):
                formula = script.get_text().strip()
                block = "mode=display" in script.get("type", "")
                display_math += int(block)
                script.replace_with(protect("$$\n" + formula + "\n$$" if block else "$" + formula + "$", block))
            else:
                report["warnings"].append(dict(article=title, warning="Removed non-math script from legacy content"))
                script.decompose()
        for anchor in list(content.select("a.headerlink")):
            anchor.decompose()

        # Protect original inline TeX before markdownify can escape it. Legacy
        # Hexo sometimes interpreted multiplication inside TeX as HTML emphasis.
        inline_count = 0

        def math_token(match):
            nonlocal inline_count
            formula = match.group(0)
            formula = re.sub(r"</?(?:em|i)>", "*", formula)
            formula = re.sub(r"</?(?:strong|b)>", "**", formula)
            formula = html.unescape(formula)
            # BeautifulSoup may have invented closing tags for tuple notation.
            formula = re.sub(r"</[a-z],[a-z]>", "", formula)
            inline_count += 1
            return str(protect(formula))

        content = BeautifulSoup(re.sub(r"(?<!\\)\$(?!\$)([^$\n]+?)(?<!\\)\$", math_token, str(content)), "html.parser")
        for code in list(content.find_all("code")):
            value = code.get_text()
            fence = "`" * max(1, max((len(x) + 1 for x in re.findall(r"`+", value)), default=1))
            code.replace_with(protect(fence + value + fence))

        # Keep old fragment identifiers so #section links still land correctly.
        heading_ids = []
        headings = list(content.find_all(re.compile(r"^h[1-6]$")))
        heading_shift = 1 if any(h.name == "h1" for h in headings) else 0
        for heading in headings:
            level = min(int(heading.name[1]) + heading_shift, 6)
            identifier = heading.get("id", "")
            heading_ids.append(identifier)
            text = convert(heading.decode_contents()).strip()
            attr = " {#" + identifier + "}" if identifier else ""
            heading.replace_with(protect("#" * level + " " + text + attr, True))

        for image in content.find_all("img"):
            original = image.get("src", "")
            absolute = urljoin("https://bakapiano.github.io" + entry["old_path"], original)
            if absolute not in cached_images:
                parsed = urlsplit(absolute)
                relative = unquote(parsed.path).lstrip("/")
                local = source / relative
                if parsed.hostname in OLD_HOSTS and local.is_file() and local.resolve().is_relative_to(source):
                    destination = site / "static" / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(local, destination)
                    cached_images[absolute] = "/" + relative
                    report["images"].append(dict(original=absolute, local="/" + relative, status="copied"))
                else:
                    name = sha(absolute)[:12] + "-" + Path(parsed.path).name
                    destination = site / "static/images/legacy-external" / name
                    try:
                        if not destination.exists():
                            request = Request(absolute, headers={"User-Agent": "Bakapiano-Blog-Migration/1.0"})
                            with urlopen(request, timeout=25) as response:
                                if not response.headers.get("Content-Type", "").startswith("image/"):
                                    raise ValueError("Remote resource is not an image")
                                data = response.read()
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            destination.write_bytes(data)
                        cached_images[absolute] = "/images/legacy-external/" + name
                        report["images"].append(dict(original=absolute, local=cached_images[absolute], status="downloaded"))
                    except Exception as exc:
                        cached_images[absolute] = absolute
                        report["images"].append(dict(original=absolute, status="unavailable", error=str(exc)))
            image["src"] = cached_images[absolute]
            if not image.get("alt"):
                image["alt"] = title + " · 插图"

        link_repairs = []
        for link in content.find_all("a", href=True):
            href = link["href"]
            if re.fullmatch(r"w\[i\][<>]0", href):
                # The old Markdown accidentally turned w[i](w[i]>0) into a
                # hyperlink. Restore the visible inequality, not a bogus URL.
                link_repairs.append(href)
                link.replace_with(protect(r"\[i\](" + href + ")"))
                continue
            if href.startswith(("#", "mailto:", "tel:")):
                continue
            absolute = urljoin("https://bakapiano.github.io" + entry["old_path"], href)
            parsed = urlsplit(absolute)
            if parsed.hostname in OLD_HOSTS:
                old_path = unquote(parsed.path).removesuffix("index.html")
                if not old_path.endswith("/"):
                    old_path += "/"
                if old_path in mapping:
                    target = 'legacy-blog/' + mapping[old_path] + '.md'
                    dest = '{{< relref "' + target + '" >}}'
                    if parsed.fragment:
                        dest += "#" + parsed.fragment
                    label = convert(link.decode_contents()).strip().replace("[", r"\[").replace("]", r"\]")
                    link.replace_with(protect("[" + label + "](" + dest + ")"))
                elif old_path == "/":
                    link["href"] = "/"

        body = convert(str(content)).strip()
        # Replacements may contain earlier tokens (e.g. math inside headings).
        for token, value in reversed(list(protected.items())):
            body = body.replace(token, value)
        if "MIGRATIONTOKEN" in body:
            raise RuntimeError(f"Unrestored migration token: {title}")
        meta = entry["meta"]
        tags = [a.get_text(strip=True) for a in entry["article"].select('a[href^="/tags/"]')]
        front = dict(title=title, date=meta["article:published_time"],
                     lastmod=meta.get("article:modified_time", meta["article:published_time"]),
                     weight=order, categories=[CATEGORY], aliases=[entry["old_path"]],
                     original_url="https://bakapiano.github.io" + entry["old_path"],
                     original_generator="Hexo", migrated_from="rendered HTML")
        if tags:
            front["tags"] = list(dict.fromkeys(tags))
        target = site / "content/legacy-blog" / (entry["slug"] + ".md")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("---\n" + yaml.safe_dump(front, allow_unicode=True, sort_keys=False) + "---\n\n" + body + "\n", encoding="utf-8")
        report["articles"].append(dict(title=title, markdown=str(target.relative_to(site)).replace("\\", "/"),
                                       old_path=entry["old_path"], new_path="/legacy-blog/" + entry["slug"].lower() + "/",
                                       date=front["date"], source_sha256=sha(entry["source"].read_text(encoding="utf-8")),
                                       code_blocks=codes, display_math=display_math, inline_math=inline_count,
                                       heading_ids=heading_ids,
                                       formatting_repairs=dict(graph_edge_notation=entry['tuple_repairs'],
                                                               duplicate_math_delimiter=entry['duplicate_math_delimiter'],
                                                               accidental_math_links=link_repairs)))
        print(f"[{order:02d}/22] {title}: {len(codes)} code blocks, {inline_count + display_math} formulas")

    # Keep the original site icon, not the theme's demonstration branding.
    icon = source / "img/favicon.svg"
    if icon.exists():
        (site / "static").mkdir(exist_ok=True)
        shutil.copy2(icon, site / "static/favicon.svg")
    (site / "migration").mkdir(exist_ok=True)
    (site / "migration/report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Migrated {len(articles)} articles. Report: migration/report.json")


if __name__ == "__main__":
    main()
