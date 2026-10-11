# Personal site

A one-page static site plus one blog page. Plain HTML and CSS, no build step, no trackers.

```
index.html                          Home: About, Blog, Publications
style.css                           Shared stylesheet
blog/jlens-qwen-template-tokens.html  The J-lens post, built from the Markdown source
blog/assets/                        The post's three figures
tools/build_post.py                 Rebuilds the blog page from the Markdown source
.nojekyll                           Tells GitHub Pages to serve the files as they are
```

## Deploy to GitHub Pages

A repository named `MPJL9.github.io` is served at `https://mpjl9.github.io`.

```
cd /Users/tliu/Desktop/Workspace/personal_webpage
git init
git add .
git commit -m "Personal site"
git branch -M main
git remote add origin git@github.com:MPJL9/MPJL9.github.io.git
git push -u origin main
```

Then on GitHub: Settings, Pages, set Source to "Deploy from a branch", branch `main`, folder `/ (root)`. The site is live a minute later. Every later `git push` redeploys it.

## Update the blog post

Edit the Markdown source, then rebuild the page:

```
python3 tools/build_post.py
```

The script reads `blog_post_published.md` from the J-lens project folder (path at the top of the script), turns the `%%% llm-output` markers into labelled boxes, gives every heading an id and builds the table of contents from them, folds the appendix tables behind "Show table" toggles (the two tables in Appendix C are named in `FOLD_LABELS` at the top of the script), and points the figures at `blog/assets/`. If a figure changes, copy the new PNG into `blog/assets/` as well. The script needs the `mistune` Python package, which is already installed.

## Links to add later

Both spots are marked with an HTML comment in `index.html`:

- Blog: the LessWrong link, once the post is approved.
- Publications: the arXiv link, once the thesis paper is submitted.

## Preview locally

```
cd /Users/tliu/Desktop/Workspace/personal_webpage
python3 -m http.server 8000
```

Then open http://localhost:8000 in a browser.
