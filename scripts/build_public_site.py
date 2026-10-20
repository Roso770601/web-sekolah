"""Build an allowlisted static preview without reading academic source files.

Only listed source files are opened. Compatibility assets and the unavailable
grades page are generated in the output, never written into the source tree.
"""
import argparse
import hashlib
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "sdn1sukamanah.my.id"
NOTICE_PATH = "nilai/nilai.html"
# Existing public pages refer to these older asset names. Fix the artifact only.
ALIASES = {
    "galeri/upacara.jpg": "galeri/upacara.webp",
    "galeri/kbm.png": "galeri/kbm.webp",
    "galeri/tka.jpg": "galeri/tka.webp",
    "galeri/pramuka.jpg": "galeri/pramuka.webp",
    "galeri/renang.jpg": "galeri/renang.webp",
    "galeri/dhuha.jpg": "galeri/dhuha.webp",
    "berita/gambar-sekolah.jpg": "gambar-sekolah.jpg",
    "img/sekolah.jpg": "gambar-sekolah.jpg",
}
GENERATED = {NOTICE_PATH, "style.css", *ALIASES}
NOTICE = '''<!doctype html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Layanan Nilai Belum Tersedia | SDN 1 Sukamanah</title>
<style>*{box-sizing:border-box}body{margin:0;padding:24px;min-height:100vh;
display:grid;place-items:center;background:#102c52;color:#fff;
font:16px/1.65 Arial,sans-serif}main{max-width:560px}h1{color:#ffdf64;
font-size:clamp(1.7rem,6vw,2.4rem);line-height:1.25}a{display:inline-block;
padding:12px 18px;background:#ffdf64;color:#102c52;border-radius:8px;
font-weight:bold}a:focus-visible{outline:3px solid white;outline-offset:4px}</style>
</head><body><main><h1>Layanan Nilai Belum Tersedia</h1>
<p>Sistem nilai belum digunakan secara resmi. Informasi pembukaan layanan
akan disampaikan oleh sekolah.</p><a href="../index.html">Kembali ke Beranda</a>
</main></body></html>'''
BASE_CSS = "*,*::before,*::after{box-sizing:border-box}img,video{max-width:100%}\n"


def permitted(name):
    p = PurePosixPath(name)
    if (not name or "\\" in name or p.is_absolute() or str(p) != name
            or any(part.startswith('.') or part == '..' for part in p.parts)):
        return False
    if name == NOTICE_PATH:
        return True  # Generated only; never copied from the source portal.
    if any(part.casefold() == "nilai" for part in p.parts):
        return False
    if name == "CNAME":
        return True
    if p.suffix.lower() == ".json":
        return name == "berita/data.json"
    return p.suffix.lower() in {".html", ".css", ".js", ".jpg", ".jpeg",
                                ".png", ".webp", ".ico", ".mp4", ".pdf", ".xml", ".txt"}


def manifest(root=ROOT):
    names = [line.strip() for line in (root / "scripts/public-files.txt")
             .read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.lstrip().startswith('#')]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate allowlist entry")
    for name in names:
        if not permitted(name) or name in GENERATED:
            raise ValueError("Forbidden source entry: " + name)
        source = root / name
        if not source.is_file() or source.is_symlink() or not source.resolve().is_relative_to(root.resolve()):
            raise ValueError("Missing or unsafe public source: " + name)
    return names


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("src", "href", "poster"):
            if attrs.get(key):
                self.refs.append(attrs[key])
        if (attrs.get("property", "") in {"og:image", "og:url"}
                or attrs.get("name", "") == "twitter:image"):
            if attrs.get("content", "").startswith("https://" + DOMAIN):
                self.refs.append(attrs["content"])


def check_links(output):
    missing = []
    def check(ref, page):
        u = urlsplit(ref)
        if not ref or ref.startswith('#') or (u.scheme and u.scheme not in {"http", "https"}):
            return
        if u.netloc and u.netloc != DOMAIN:
            return  # Never request external services, including CCTV and WhatsApp.
        if not u.path:
            return
        target = output / unquote(u.path).lstrip('/') if u.path.startswith('/') or u.netloc else page.parent / unquote(u.path)
        if not target.resolve().is_relative_to(output.resolve()):
            missing.append(page.relative_to(output).as_posix() + ": path escapes artifact")
        elif not (target.is_file() or target.is_dir() and (target / "index.html").is_file()):
            missing.append(page.relative_to(output).as_posix() + ": " + u.path)
    for page in output.rglob("*.html"):
        text = page.read_text(encoding="utf-8-sig")
        parser = References()
        parser.feed(text)
        for ref in parser.refs:
            check(ref, page)
        for ref in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", text):
            check(ref, page)
    for css in output.rglob("*.css"):
        for ref in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", css.read_text(encoding="utf-8-sig")):
            check(ref, css)
    # News links are generated by JavaScript, so check them separately.
    for item in json.loads((output / "berita/data.json").read_text(encoding="utf-8-sig")):
        check("berita/" + item["link"], output / "index.html")
    if missing:
        raise ValueError("Broken public references:\n" + "\n".join(sorted(set(missing))))


def validate(output, root=ROOT):
    names = manifest(root)
    expected = set(names) | GENERATED
    actual = set()
    for file in output.rglob('*'):
        if file.is_symlink():
            raise ValueError("Symlink rejected")
        if file.is_file():
            name = file.relative_to(output).as_posix()
            if not permitted(name) or name not in expected:
                raise ValueError("Unexpected or forbidden artifact file: " + name)
            actual.add(name)
    if actual != expected:
        raise ValueError("Artifact file set does not match the explicit allowlist")
    if (output / "CNAME").read_text().strip() != DOMAIN:
        raise ValueError("Unexpected domain")
    if (output / NOTICE_PATH).read_text(encoding="utf-8") != NOTICE:
        raise ValueError("Grades notice was modified")
    if (output / "style.css").read_text(encoding="utf-8") != BASE_CSS:
        raise ValueError("Generated CSS was modified")
    for name in names:
        if (output / name).read_bytes() != (root / name).read_bytes():
            raise ValueError("Public source was modified in artifact: " + name)
    for dest, source in ALIASES.items():
        if (output / dest).read_bytes() != (root / source).read_bytes():
            raise ValueError("Compatibility asset mismatch: " + dest)
    check_links(output)
    return sorted(actual)


def build(output, root=ROOT):
    output = output.resolve()
    if output.exists():
        raise ValueError("Use a new output directory; existing directories are never overwritten")
    names = manifest(root)
    if (root / "CNAME").read_text().strip() != DOMAIN:
        raise ValueError("Unexpected source domain")
    for name in names:
        dest = output / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, dest)
    for dest, source in ALIASES.items():
        target = output / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / source, target)
    (output / NOTICE_PATH).parent.mkdir(parents=True, exist_ok=True)
    (output / NOTICE_PATH).write_text(NOTICE, encoding="utf-8", newline="\n")
    (output / "style.css").write_text(BASE_CSS, encoding="utf-8", newline="\n")
    return validate(output, root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    files = validate(args.output.resolve()) if args.check_only else build(args.output)
    if args.report:
        report = args.report.resolve()
        if report.is_relative_to(args.output.resolve()):
            raise ValueError("Report must remain outside the artifact")
        report.write_text(json.dumps({"domain": DOMAIN, "files": [
            {"path": name, "sha256": hashlib.sha256((args.output / name).read_bytes()).hexdigest()}
            for name in files]}, indent=2), encoding="utf-8")
    print(f"PASS: {len(files)} allowlisted public files; academic datasets excluded; local references valid.")
