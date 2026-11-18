# Putting LabLayout on your website

`dist/` is a complete static site. It has no server code, build step or dependencies:

| File | What it is |
|---|---|
| `index.html` | landing page |
| `builder.html` | the room builder (everything inlined, one file) |
| `example-tracker.html` | sample tracker |
| `llms.txt`, `AI_LAYOUT_GUIDE.md` | instructions that AI agents can find |

## Option 1: upload the folder

Run `python build.py`, then upload the contents of `dist/` to any static host or subfolder, for example `yoursite.com/lablayout/`. Hosts that work include GitHub Pages, Netlify, Vercel, Cloudflare Pages, or plain FTP. All links are relative, so a subfolder works.

- **GitHub Pages:** go to Settings → Pages → Deploy from branch, then pick `main` and `/dist`. GitHub only offers `/` or `/docs` there, so you can instead copy `dist/` into the `docs/` folder or use a Pages action.
- **Netlify / Vercel / Cloudflare Pages:** set the build command to `python build.py` and the output directory to `dist`.

## Option 2: embed in an existing page

```html
<iframe src="/lablayout/builder.html" title="LabLayout room builder"
        style="width:100%;height:85vh;border:0;border-radius:8px"
        allow="clipboard-write"></iframe>
```

`allow="clipboard-write"` lets the **Copy prompt** and **Copy spec** buttons work inside the frame. Saved projects live in the visitor's browser (localStorage) under your site's origin.

To open the embed with a ready-made layout, add `#layout=<base64url JSON>` to the `src`.

## Notes

- Every visitor's data stays in their own browser. Nothing is sent to your server unless they set up Supabase sync themselves.
- Exported trackers are standalone files, so visitors download them and can use them offline.
- Rebuild (`python build.py`) and re-upload after you change anything in `src/`.
