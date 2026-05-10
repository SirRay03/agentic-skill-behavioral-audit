#!/usr/bin/env python3
"""Convert report.md to a styled HTML file for browser print-to-PDF.

Output is a single self-contained HTML file with embedded CSS — no external
deps, prints cleanly to PDF in Chrome/Edge/Firefox.

Usage:
    python3 harness/md-to-html.py report.md > report.html
"""
import sys
import markdown

CSS = """
@page { size: A4; margin: 2cm 2cm 2.5cm 2cm; }
body { font-family: Georgia, "Times New Roman", serif; font-size: 11pt; line-height: 1.45;
       color: #111; max-width: 720px; margin: 1.5em auto; padding: 0 1em; }
h1 { font-size: 19pt; font-weight: 700; border-bottom: 2px solid #111; padding-bottom: 0.2em; margin-top: 0; }
h2 { font-size: 14pt; font-weight: 700; margin-top: 1.5em; border-bottom: 1px solid #888; padding-bottom: 0.15em; }
h3 { font-size: 12pt; font-weight: 700; margin-top: 1.2em; color: #222; }
h4 { font-size: 11pt; font-weight: 700; margin-top: 0.8em; }
p { margin: 0.5em 0; text-align: justify; }
strong { font-weight: 700; }
em { font-style: italic; }
hr { border: none; border-top: 1px solid #888; margin: 2em 0; }
code { font-family: "JetBrains Mono", Consolas, "Courier New", monospace;
       font-size: 0.92em; background: #f4f4f4; padding: 0.1em 0.3em; border-radius: 3px; }
pre { background: #f4f4f4; padding: 0.6em 0.9em; border-radius: 4px; overflow-x: auto; font-size: 0.9em; line-height: 1.35; }
pre code { background: none; padding: 0; font-size: 1em; }
blockquote { border-left: 3px solid #888; margin: 0.6em 0; padding: 0.1em 1em;
             color: #555; background: #fafafa; }
table { border-collapse: collapse; width: 100%; margin: 0.7em 0; font-size: 0.94em; }
th, td { border: 1px solid #aaa; padding: 0.35em 0.55em; text-align: left; vertical-align: top; }
th { background: #eee; font-weight: 700; }
ul, ol { margin: 0.5em 0; padding-left: 1.5em; }
li { margin: 0.15em 0; }
figure { margin: 1.2em 0; padding: 0.5em 0; text-align: center; page-break-inside: avoid; }
figure img { max-width: 100%; height: auto; border: 1px solid #ddd; background: #fff; }
figcaption { font-size: 0.88em; color: #444; margin-top: 0.5em; padding: 0 0.5em;
             text-align: justify; line-height: 1.4; }
@media print {
  h2 { page-break-after: avoid; }
  table, pre, figure { page-break-inside: avoid; }
  body { font-size: 10pt; }
}
"""

def main():
    if len(sys.argv) < 2:
        print("usage: md-to-html.py <input.md>", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        md = f.read()
    html_body = markdown.markdown(md, extensions=["tables", "fenced_code", "toc"])
    print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Behavioural Auditor for Agentic Skills — Rayhan Putra</title>
<style>{CSS}</style>
</head>
<body>
{html_body}
</body>
</html>""")


if __name__ == "__main__":
    main()
