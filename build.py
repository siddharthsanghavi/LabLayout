"""Build LabLayout: inlines the tracker template into the builder.

    python build.py

Outputs:
    dist/builder.html          - the room builder (open in any browser)
    dist/example-tracker.html  - the HatchBridge lab tracker (the template's built-in example)
"""
import json, pathlib, re

root = pathlib.Path(__file__).parent
tracker = (root / "src" / "tracker.html").read_text(encoding="utf-8")
builder = (root / "src" / "builder.html").read_text(encoding="utf-8")

assert "/*LABLAYOUT_CONFIG*/" in tracker and "/*END_CONFIG*/" in tracker, "tracker template is missing its config markers"
assert "/*TRACKER_TEMPLATE*/null" in builder, "builder is missing the template placeholder"

# JSON-encode the template and keep "</script>" from closing the builder's own script tag
embedded = json.dumps(tracker).replace("</", "<\\/")
out = builder.replace("/*TRACKER_TEMPLATE*/null", "/*TRACKER_TEMPLATE*/" + embedded, 1)

# Bundle every library pack in library/*.json (add a file or append items to add equipment)
assert "/*LIBRARY_PACKS*/[]" in out, "builder is missing the library placeholder"
packs = []
for p in sorted((root / "library").glob("*.json")):
    pack = json.loads(p.read_text(encoding="utf-8"))
    keys = [it["k"] for c in pack["categories"] for it in c["items"]]
    dup = {k for k in keys if keys.count(k) > 1}
    assert not dup, f"{p.name}: duplicate keys {sorted(dup)}"
    for c in pack["categories"]:
        for it in c["items"]:
            assert it.get("w", 0) > 0 and it.get("h", 0) > 0 and len(it.get("fp", [])) == 2, f"{p.name}: {it.get('k')} needs w, h and fp"
    packs.append(pack)
out = out.replace("/*LIBRARY_PACKS*/[]", "/*LIBRARY_PACKS*/" + json.dumps(packs, ensure_ascii=False).replace("</", "<\\/"), 1)
n_items = sum(len(c["items"]) for p in packs for c in p["categories"])
print(f"bundled {len(packs)} library pack(s), {n_items} items")

dist = root / "dist"
dist.mkdir(exist_ok=True)
(dist / "builder.html").write_text(out, encoding="utf-8")
(dist / "example-tracker.html").write_text(tracker, encoding="utf-8")
# Static-site extras so dist/ can be uploaded to any web host as-is
(dist / "index.html").write_text((root / "src" / "index.html").read_text(encoding="utf-8"), encoding="utf-8")
(dist / "llms.txt").write_text((root / "llms.txt").read_text(encoding="utf-8").replace("dist/builder.html", "builder.html").replace("](docs/AI_LAYOUT_GUIDE.md)", "](AI_LAYOUT_GUIDE.md)"), encoding="utf-8")
(dist / "AI_LAYOUT_GUIDE.md").write_text((root / "docs" / "AI_LAYOUT_GUIDE.md").read_text(encoding="utf-8"), encoding="utf-8")
print(f"built dist/builder.html ({len(out)//1024} KB) and dist/example-tracker.html ({len(tracker)//1024} KB)")
