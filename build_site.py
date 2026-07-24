#!/usr/bin/env python3
"""Build CookCLI output and apply Recipe Hopper's static-site additions."""

import argparse
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "_site"

parser = argparse.ArgumentParser()
parser.add_argument("--cook", default="cook")
args = parser.parse_args()

if SITE.exists():
    shutil.rmtree(SITE, onerror=lambda function, path, _: (
        os.chmod(path, stat.S_IWRITE), function(path)
    ))
subprocess.run([
    args.cook, "build", "web", "--base-path", str(ROOT / "recipes"),
    "--base-url", "/recipe-hopper/",
], cwd=ROOT, check=True)

css = (ROOT / "site.css").read_text(encoding="utf-8")
with (SITE / "static/css/custom-styles.css").open("a", encoding="utf-8") as output:
    output.write("\n" + css)
shutil.copy2(ROOT / "planner.html", SITE / "planner.html")

link = '<a class="planner-fab print:hidden" href="/recipe-hopper/planner.html">Weekly plan</a>'
for page in SITE.rglob("*.html"):
    text = page.read_text(encoding="utf-8")
    text = re.sub(
        r'<a href="[^"]+\.cook"\s+download.*?title="Download \.cook source".*?</a>',
        "",
        text,
        flags=re.S,
    )
    page.write_text(text.replace("</body>", link + "\n</body>"), encoding="utf-8")
