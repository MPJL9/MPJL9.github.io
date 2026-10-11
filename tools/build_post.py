"""Convert the J-lens blog post markdown into the site's blog page."""
import html as htmllib
import re, sys
import mistune

SRC = "/Users/tliu/Desktop/Workspace/J-lens_lie_studies/current/redo_analysis/blog_post_published.md"
OUT = "/Users/tliu/Desktop/Workspace/personal_webpage/blog/jlens-qwen-template-tokens.html"

ALT = {
    "F_template_strip.png": "Qwen's chat template tokens, with the newline after the response marked.",
    "lie_flagged_by_10_families.png": "The J-lens readout at the newline token of one lie transcript, with lie-side words highlighted.",
    "F_tokens_after_answer.png": "Seven AUROC scores in token order with 95% intervals.",
}

# Tables in the appendices sit behind a "Show table" toggle. Where an appendix
# has several tables in a row, these name them, in order. The script stops if
# the count no longer matches the source.
FOLD_LABELS = {
    "Appendix C": ["Gemma-3-12B", "Gemma-3-27B"],
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
    numeric = re.fullmatch(r"[\d\s().%/|,;:\-–]*(to[\d\s().%/|,;:\-–]*)*", text)
    if text and (numeric or len(text) <= 14):
        return f'<td class="nw">{inner}</td>'
    return mm.group(0)
body = re.sub(r"<td>(.*?)</td>", mark_cell, body, flags=re.S)

# Let wide tables scroll sideways on a phone.
body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")

# Give every section heading an id, and collect the table of contents.
toc = []        # (level, id, heading html)
used_ids = set()

def heading_id(inner):
    text = htmllib.unescape(re.sub(r"<[^>]+>", "", inner))
    m = re.match(r"Appendix ([A-Z])\b", text)
    if m:
        base = "appendix-" + m.group(1).lower()
    else:
        text = re.sub(r"^\d+(\.\d+)*\.?\s*(\(\d+\)\s*)?", "", text)   # "3.1 " or "5.1 (2) "
        text = text.replace("'", "").replace("’", "")
        base = "-".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split()[:8]) or "section"
    hid, n = base, 2
    while hid in used_ids:
        hid = f"{base}-{n}"
        n += 1
    used_ids.add(hid)
    return hid

def add_id(mm):
    level, inner = mm.group(1), mm.group(2)
    hid = heading_id(inner)
    toc.append((int(level), hid, inner))
    return f'<h{level} id="{hid}">{inner}</h{level}>'
body = re.sub(r"<h([23])>(.*?)</h\1>", add_id, body, flags=re.S)

# Nest the h3 entries under their h2.
groups = []
for level, hid, inner in toc:
    if level == 2 or not groups:
        groups.append(((hid, inner), []))
    else:
        groups[-1][1].append((hid, inner))
lines = []
for (hid, inner), subs in groups:
    lines.append(f'<li><a href="#{hid}">{inner}</a>')
    if subs:
        lines.append("<ol>")
        lines += [f'<li><a href="#{h}">{t}</a></li>' for h, t in subs]
        lines.append("</ol>")
    lines.append("</li>")
toc_list = "\n".join(lines)

# Fold the tables in the appendices behind a "Show table" toggle.
TABLE = r'<div class="table-wrap">.*?</table></div>'

def fold_tables(section, name):
    labels = FOLD_LABELS.get(name)
    tables = re.findall(TABLE, section, flags=re.S)
    if labels is not None and len(labels) != len(tables):
        sys.exit(f"{name} has {len(tables)} tables but FOLD_LABELS names {len(labels)}")
    counter = iter(range(len(tables)))
    def wrap(mm):
        i = next(counter)
        table = mm.group(0)
        rows = len(re.findall(r"<tr>", table.split("<tbody>", 1)[-1]))
        what = f"the {labels[i]} table" if labels else "table"
        return (f'<details class="fold">\n<summary>'
                f'<span class="fold-show">Show {what}</span><span class="fold-hide">Hide {what}</span>'
                f' <span class="fold-note">({rows} rows)</span></summary>\n{table}\n</details>')
    return re.sub(TABLE, wrap, section, flags=re.S)

parts = []
for part in re.split(r"(?=<h2[ >])", body):
    m = re.match(r"<h2[^>]*>(Appendix [A-Z])\b", part)
    parts.append(fold_tables(part, m.group(1)) if m else part)
body = "".join(parts)

# Marks the section being read in the table of contents, and closes the
# contents box on narrow screens, where it sits above the post.
SCRIPT = """<script>
(function () {
  var toc = document.querySelector('.toc');
  var box = toc.querySelector('details');
  var narrow = window.matchMedia('(max-width: 919px)');  // one below the sidebar breakpoint in style.css
  if (narrow.matches) box.removeAttribute('open');
  var links = [].slice.call(toc.querySelectorAll('a[href^="#"]'));
  var heads = links.map(function (a) { return document.getElementById(a.hash.slice(1)); });
  var current = -1;
  function update() {
    var pick = -1;
    for (var i = 0; i < heads.length; i++) {
      if (heads[i] && heads[i].getBoundingClientRect().top <= 96) pick = i;
    }
    if (pick === current) return;
    if (current >= 0) links[current].classList.remove('is-active');
    current = pick;
    if (pick < 0) return;
    var a = links[pick];
    a.classList.add('is-active');
    if (!narrow.matches && toc.scrollHeight > toc.clientHeight) {
      var r = a.getBoundingClientRect(), t = toc.getBoundingClientRect();
      if (r.top < t.top + 24 || r.bottom > t.bottom - 24) toc.scrollTop += r.top - t.top - t.height / 2;
    }
  }
  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
  update();
})();
</script>"""

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Tianxiang (Jimmy) Liu</title>
<meta name="description" content="Some findings on the template tokens of Qwen 3.6 27B using Jacobian Lens.">
<link rel="stylesheet" href="../style.css?v=2">
</head>
<body>
<header>
<a class="name" href="../index.html">Tianxiang (Jimmy) Liu</a>
</header>
<main class="post">
<article>
<h1>{title}</h1>
<p class="post-meta">October 2026</p>
<nav class="toc" aria-label="Contents">
<details class="toc-box" open>
<summary>Contents</summary>
<ol class="toc-list">
{toc_list}
</ol>
</details>
</nav>
<div class="post-body">
{body}
</div>
</article>
</main>
{SCRIPT}
</body>
</html>
"""
open(OUT, "w", encoding="utf-8").write(page)
print("wrote", OUT, len(page), "bytes")
