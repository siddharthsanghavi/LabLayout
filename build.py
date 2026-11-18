"""Build CribOps: inlines the tracker template into the builder.

    python build.py

Outputs:
    dist/builder.html          - the room builder (open in any browser)
    dist/example-tracker.html  - the HatchBridge lab tracker (the template's built-in example)
"""
import json, pathlib, re

root = pathlib.Path(__file__).parent
tracker = (root / "src" / "tracker.html").read_text(encoding="utf-8")
builder = (root / "src" / "builder.html").read_text(encoding="utf-8")

assert "/*CRIBOPS_CONFIG*/" in tracker and "/*END_CONFIG*/" in tracker, "tracker template is missing its config markers"
assert "/*TRACKER_TEMPLATE*/null" in builder, "builder is missing the template placeholder"

# JSON-encode the template and keep "</script>" from closing the builder's own script tag
embedded = json.dumps(tracker).replace("</", "<\\/")
out = builder.replace("/*TRACKER_TEMPLATE*/null", "/*TRACKER_TEMPLATE*/" + embedded, 1)

dist = root / "dist"
dist.mkdir(exist_ok=True)
(dist / "builder.html").write_text(out, encoding="utf-8")
(dist / "example-tracker.html").write_text(tracker, encoding="utf-8")
print(f"built dist/builder.html ({len(out)//1024} KB) and dist/example-tracker.html ({len(tracker)//1024} KB)")
