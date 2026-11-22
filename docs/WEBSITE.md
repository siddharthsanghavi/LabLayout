# Putting LabLayout on your website

`site/` is a complete static site. It has no server code, build step or dependencies:

| File | What it is |
|---|---|
| `index.html` | landing page |
| `builder.html` | the app: layout editor and inventory (everything inlined, one file) |
| `example-tracker.html` | sample tracker |
| `llms.txt`, `AI_LAYOUT_GUIDE.md` | instructions that AI agents can find |

## Option 1: upload the folder

Upload the contents of `site/` to any static host or subfolder, for example `yoursite.com/lablayout/`. Hosts that work include GitHub Pages, Netlify, Vercel, Cloudflare Pages, or plain FTP. All links are relative, so a subfolder works.

- **GitHub Pages:** go to Settings → Pages → Deploy from branch, then pick `main`. GitHub only offers `/` or `/docs` there, so copy `site/` into `docs/` or use a Pages action that publishes `site/`.
- **Netlify / Vercel / Cloudflare Pages:** leave the build command empty and set the output (publish) directory to `site`.

## Option 2: embed in an existing page

```html
<iframe src="/lablayout/builder.html" title="LabLayout"
        style="width:100%;height:85vh;border:0;border-radius:8px"
        allow="clipboard-write"></iframe>
```

`allow="clipboard-write"` lets the **Copy prompt** and **Copy spec** buttons work inside the frame. Saved projects live in the visitor's browser (localStorage) under your site's origin.

To open the embed with a ready-made layout, add `#layout=<base64url JSON>` to the `src`.

## Notes

- Every visitor's data stays in their own browser. Nothing is sent to your server unless they set up Supabase sync themselves.
- Exported trackers are standalone files, so visitors download them and can use them offline.
- After you change anything in `site/`, re-upload it. There is no build step.
