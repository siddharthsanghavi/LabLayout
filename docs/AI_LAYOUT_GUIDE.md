# Generating LabLayout layouts with an AI (Claude, ChatGPT, …)

LabLayout reads a small JSON **layout spec**. An AI writes the spec, and the builder turns it into a room you can edit and then export as a tracker.

## Three ways in

1. **Copy-paste (any chatbot).** In the builder click **🤖 AI layout → Copy prompt**. Paste it into the chat and describe your room. Paste the reply back and click **Build it**. Prose and ```json fences around the reply are ignored. If the spec has mistakes, **Copy fix-up request** gives you a message listing the errors to send back to the bot.
2. **Link.** Open `builder.html#layout=<base64url of the spec JSON>` and the layout loads straight away. This suits agents that can open URLs.
3. **Browser automation (agents with a browser/JS tool).** Use `window.LabLayout` on the builder page:

| Call | Returns |
|---|---|
| `LabLayout.prompt()` | the full prompt text, catalogue included |
| `LabLayout.catalog()` | library pieces, with kinds, footprints and default cells |
| `LabLayout.validate(spec)` | `{errors:[…], warnings:[…]}` |
| `LabLayout.importSpec(spec or string)` | `{ok, units}` or `{ok:false, errors}`; can be undone in the UI |
| `LabLayout.exportSpec()` | the current room as a spec (lossless: ids are kept, so tracker data survives) |
| `LabLayout.exportTracker()` | downloads the tracker HTML |

## The spec

Units: positions, footprints and room sizes are in **feet**. Furniture fronts and cells are in **inches**. The origin is the room's top-left corner, x goes right and y goes down. `x`/`y` give an item's top-left corner.

```json
{
  "lablayout": 1,
  "title": "Electronics lab",
  "room": { "width": 14, "depth": 20 },
  "items": [
    { "kind": "door", "name": "Door", "x": 5, "y": 19.6, "w": 3, "d": 0.4 },
    { "kind": "bench2", "name": "Bench A", "x": 0, "y": 0, "tab": "Benches",
      "drawers": ["Resistors", "Capacitors", "Connectors"],
      "on_top": ["hakko", "monitor"] },
    { "kind": "flam30", "name": "Solvents", "x": 12.5, "y": 6, "rotate": 90 },
    { "kind": "custom", "name": "Parts cabinet", "x": 7, "y": 0,
      "footprint": [3, 1.5], "front": [36, 30], "finish": "maple", "worktop": true,
      "cells": [
        { "name": "Screws", "type": "drawer", "x": 0,  "y": 0,  "w": 18, "h": 6 },
        { "name": "Nuts",   "type": "drawer", "x": 18, "y": 0,  "w": 18, "h": 6 },
        { "name": "Tools",  "type": "door",   "x": 0,  "y": 6,  "w": 36, "h": 24 }
      ] }
  ]
}
```

**Room:** either `{"width", "depth"}` or `{"corners": [[x,y], …]}`. A corner can be written `[x, y, fillet_radius, arc_depth]` to round it.

**Item fields**

| Field | Meaning |
|---|---|
| `kind` | a library kind (table below), `"custom"`, or `"door"` |
| `name`, `tab`, `map_label` | display name, tracker tab, and label on the floor map |
| `x`, `y` | top-left corner of the footprint, in feet |
| `rotate` | 0/90/180/270 (90 and 270 swap the width and depth) |
| `footprint` | `[w, d]` in feet. Required for custom; optional override for machines and fixtures |
| `drawers` | names given to the library piece's cells, in order |
| `layout` | `{"preset", "n", "cols"}` to change a storage piece's drawer layout |
| `on_top` | machine/fixture kinds placed on a bench or cabinet |
| `finish`, `color`, `look` | appearance: maple, oak, black, cabinet, husky, … |
| `id` | optional stable id. Keep it when editing an exported spec so inventory stays attached |

**Custom cells:** `type` is one of `drawer | deep | door | shelf | full`. Cells must fit inside `front` and must not overlap. Gaps are allowed.

## Rules the validator enforces

- `room`, `items`, and numeric `x`/`y` are required.
- An unknown `kind` is an error, and the message suggests close matches.
- `on_top` must list machine or fixture kinds.
- Custom pieces need `footprint`, `front`, and at least one cell. Cells must fit and not overlap.

Good practice, not enforced: keep items inside the room, leave about 3 ft of aisle, and put flammable cabinets away from the door.

## Library kinds

| kind | name | footprint ft | role |
|---|---|---|---|
| `uline60` | Steel workbench 60" | 5 × 2.5 | storage |
| `uline72` | Steel workbench 72" | 6 × 2.5 | storage |
| `bench2` | Workbench, 2 drawer stacks 72" | 6 × 2.5 | storage |
| `open72` | Open workbench 72" (lower shelf) | 6 × 2.5 | storage |
| `husky72` | Husky 72" mobile workbench | 6 × 1.66 | storage |
| `chest46` | Tool chest 46" (8 drawers) | 3.83 × 1.5 | storage |
| `cart` | Rolling tool cart | 2.5 × 1.5 | storage |
| `flam17` / `flam30` / `flam45` | Flammable cabinet 17/30/45 gal | 3.6 × 1.5 | storage |
| `store` | Storage cabinet 36" (2-door) | 3 × 1.5 | storage |
| `wallcab` | Wall cabinet 30" | 2.5 × 1 | storage |
| `drawercab` | Drawer cabinet (10) | 2.5 × 2 | storage |
| `wire` | Wire shelving 48" | 4 × 1.5 | storage |
| `bins` | Bin rack 36" (4×4) | 3 × 1 | storage |
| `tower36` | Storage tower 36" | 3 × 1.67 | storage |
| `locker6` | Locker cabinet, 6 doors | 3.75 × 1.5 | storage |
| `credenza72` | Credenza 72" | 6 × 2 | storage |
| `desk72` | Desk 72" with drawers | 6 × 2.5 | storage |
| `ped` | Mobile pedestal | 1.25 × 1.67 | storage |
| `prusa` | Prusa MK4 (enclosure) | 2.2 × 2 | machine |
| `bambu` | Bambu Lab X1C | 1.3 × 1.4 | machine |
| `form4` / `wash` / `cure` | Formlabs Form 4 / Wash / Cure | ~1.2 × 1.2 | machine |
| `glowforge` | Glowforge Pro HD | 3.2 × 1.75 | machine |
| `cnc` | Desktop CNC router | 2.5 × 2.5 | machine |
| `hakko` | Hakko FX-951 soldering | 0.5 × 0.6 | machine |
| `monitor` / `pc` | Monitor / Desktop PC | 1.8 × 0.7 / 0.6 × 1.3 | machine |
| `sink` | Sink + eyewash | 1.7 × 1.5 | fixture |
| `ext` | Fire extinguisher | 0.75 × 0.3 | fixture |
| `eyewash` | Eyewash station | 0.9 × 0.5 | fixture |
| `aid` | First aid kit + towels | 1.3 × 0.3 | fixture |
| `trash` | Trash can | 1.25 × 1.25 | fixture |
| `door` | Door | 3 × 0.4 | map only |

The live list, including the user's own saved pieces, comes from `LabLayout.catalog()` or the copied prompt.
