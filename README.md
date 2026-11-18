# CribOps

Lay out any lab or tool crib, then generate a self-contained inventory tracker for it.

## What's here

| File | What it is |
|---|---|
| `dist/builder.html` | **The room builder.** Open it in a browser — no install. |
| `dist/example-tracker.html` | The HatchBridge prototyping lab tracker (the built-in example). |
| `src/builder.html` | Builder source. |
| `src/tracker.html` | Tracker template. Its room/furniture layout lives in one JSON block between `/*CRIBOPS_CONFIG*/` and `/*END_CONFIG*/`. |
| `build.py` | Inlines the tracker template into the builder → `dist/`. |

## Using the builder

1. Open `dist/builder.html`.
2. **Room** — type a width × depth and press *Rectangle*, press *Draw walls* and click corners (walls snap straight; click the first corner to close), or paste corner coordinates.
3. **Library** — drag pieces onto the plan:
   - *Workbenches & tool chests* — steel workbenches, Husky 72" 11-drawer, tool chest, rolling cart
   - *Cabinets & shelving* — flammable cabinets (17/30/45 gal), storage & wall cabinets, drawer cabinet, wire shelving, bin rack
   - *Machines* — Prusa MK4 (enclosure), Bambu X1C, Form 4, Form Wash/Cure V2, Glowforge Pro HD, desktop CNC, Hakko FX-951, monitor, PC
   - *Room fixtures* — sink + eyewash, fire extinguisher, eyewash station, first aid, trash can, door
   
   Drop a machine or fixture **on** a bench/wall group to put it on top; drop it on the floor to give it its own spot. Machines bring their consumable slots with them (spool, resin tank + cartridge, IPA, Glowforge material). On a phone, tap a library item to add it to the middle of the room.
4. **Click a piece** to rename it, set its tab label, move/resize/rotate it, change its front size, pick a drawer/shelf layout (or set how many), rename each drawer, toggle worktop and under-space storage, reorder or remove machines, or stack a printer ×2.
5. **▶ Preview tracker** to try it (phone or desktop width).
6. **⬇ Export tracker HTML** — saves `<room-name>-tracker.html`, a single file that works offline on any phone or computer.

*Save project* / *Open project* keep the layout as a `.cribops.json` file so you can edit it later. The builder also autosaves in your browser. *Load example* opens the HatchBridge lab.

The builder warns you if anything sits outside the walls or overlaps.

## The tracker it generates

Everything from the HatchBridge tracker, laid out for your room: room-map and per-unit tabs, to-scale front views, drag-and-drop with stacks handing out one at a time, search, quantities, consumable levels, machine slots, checkout, damage and used-up reporting, an activity log with a usage summary, and protected deletes.

**Re-exporting keeps data.** Tracker data is stored in each browser under the room name. If you re-export after changing the layout, items in drawers that still exist stay put, and items from removed drawers land in *Unsorted*.

**Data is per browser.** Each phone or computer keeps its own copy. Shared storage (one inventory for everyone) is a planned next step.

## Rebuilding

After editing anything in `src/`:

```
python build.py
```

## Roadmap

- Windows `.exe` (Electron wrapper around the exported tracker)
- Shared/synced storage across devices
- Custom library pieces from the builder
