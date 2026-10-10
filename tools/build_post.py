"""Convert the J-lens blog post markdown into the site's blog page."""
import re, sys
import mistune

SRC = "/Users/tliu/Desktop/Workspace/J-lens_lie_studies/current/redo_analysis/blog_post_published.md"
OUT = "/Users/tliu/Desktop/Workspace/personal_webpage/blog/jlens-qwen-template-tokens.html"

ALT = {
    "F_template_strip.png": "Qwen's chat template tokens, with the newline after the response marked.",
    "lie_flagged_by_10_families.png": "The J-lens readout at the newline token of one lie transcript, with lie-side words highlighted.",
    "F_tokens_after_answer.png": "Seven AUROC scores in token order with 95% intervals.",
}

src = open(SRC, encoding="utf-8").read()

# Drop the source note (an HTML comment) at the top of the file.
src = re.sub(r"\A\s*<!--.*?-->\s*", "", src, flags=re.S)

# Pull out the title line.
m = re.match(r"# (.*)\n", src)
title = m.group(1).strip()
src = src[m.end():]

# %%% llm-output model="X" ... %%% /llm-output  ->  labelled shaded block
src = re.sub(
    r'^%%% llm-output model="([^"]+)"[ \t]*$',
    lambda mm: f'<div class="llm-output">\n<p class="llm-label">Written by {mm.group(1)}</p>\n',
    src, flags=re.M)
src = re.sub(r"^%%% /llm-output[ \t]*$", "</div>", src, flags=re.M)

# ![](raw github url)*caption*  ->  <figure> with a local image
def fig(mm):
    name = mm.group(1)
    cap = mm.group(2).strip()
    alt = ALT.get(name, "")
    return f'<figure>\n<img src="assets/{name}" alt="{alt}">\n<figcaption>{cap}</figcaption>\n</figure>'
src = re.sub(r"^!\[\]\(\S+?/blogpost_asset/([^)]+)\)\*(.*?)\*[ \t]*$", fig, src, flags=re.M)

md = mistune.create_markdown(escape=False, plugins=["table"])
body = md(src)

# Escaped pipes inside code spans in table cells keep their backslash; drop it.
body = body.replace('\\|', '|')

# Keep numeric and short cells on one line; let long text cells wrap.
def mark_cell(mm):
    inner = mm.group(1)
    text = re.sub(r"<[^>]+>", "", inner).strip()
    numeric = re.fullmatch(r"[\d\s().%/|,;:\-\u2013]*(to[\d\s().%/|,;:\-\u2013]*)*", text)
    if text and (numeric or len(text) <= 14):
        return f'<td class="nw">{inner}</td>'
    return mm.group(0)
body = re.sub(r"<td>(.*?)</td>", mark_cell, body, flags=re.S)

# Let wide tables scroll sideways on a phone.
body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Tianxiang (Jimmy) Liu</title>
<meta name="description" content="Some findings on the template tokens of Qwen 3.6 27B using Jacobian Lens.">
<link rel="stylesheet" href="../style.css">
</head>
<body>
<header>
<a class="name" href="../index.html">Tianxiang (Jimmy) Liu</a>
</header>
<main class="post">
<article>
<h1>{title}</h1>
<p class="post-meta">October 2026</p>
<div class="post-body">
{body}
</div>
</article>
</main>
</body>
</html>
"""
open(OUT, "w", encoding="utf-8").write(page)
print("wrote", OUT, len(page), "bytes")
