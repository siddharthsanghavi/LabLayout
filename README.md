# LabLayout

Lay out your labs and tool cribs and run their inventory in the same app. One HTML file, works offline, in feet/inches or metres.

## What's here

| File | What it is |
|---|---|
| `dist/builder.html` | **The app**: layout editor and inventory in one file. Open it in a browser, no install. |
| `dist/example-tracker.html` | The HatchBridge prototyping lab tracker (the built-in example). |
| `src/builder.html` | App source. |
| `src/tracker.html` | Tracker template. Its room/furniture layout lives in one JSON block between `/*LABLAYOUT_CONFIG*/` and `/*END_CONFIG*/`. |
| `build.py` | Inlines the tracker template into the builder → `dist/`. |

## Using LabLayout

Open `dist/builder.html`. The switch at the top has two modes:

- **✏️ Edit layout**: draw the room and arrange furniture (steps below).
- **📦 Inventory**: use the room's tracker in the same window: check items in and out, consumables, reorder list, activity log. Inventory is stored in the browser, so switching back to Edit and changing the layout keeps it. Drawers you keep keep their items, and items from deleted drawers move to *Unsorted*. The app reopens in whichever mode you used last.

**Rooms**: a project can hold several rooms, shown as tabs under the header. **＋ Room** adds an empty room, **⧉ Copy room** duplicates the current one, and the name box renames it. Each room keeps its own inventory. There are two file formats:

| | Export | Import |
|---|---|---|
| **Layout JSON** (`.lablayout.json`): the full layout, every room | **⬇ Export layout JSON** (header) | **⬆ Import layout JSON** replaces the open layout. A room JSON opens as a one-room layout |
| **Room JSON** (`.room.json`): one room | **⬇ Room JSON** (room bar) | **⬆ Import room** adds it as a new room. A layout JSON adds all its rooms, and AI layout specs work too |
 `*.room.json` files and the `local/` folder are git-ignored, so your own room files stay out of the repo.

**Metric**: **📏 ft · in** switches the whole app to metres and centimetres: room size, wall lengths, positions, footprints, front sizes and the designer. You can always type `2.4 m`, `240 cm` or `2400 mm`, and in metric mode a bare number means metres. Layouts are stored internally in feet and inches, so switching units never changes the design.

### Editing a room

1. Open `dist/builder.html` and pick ✏️ Edit layout.
2. **Room**: type a width × depth and press *Rectangle*, sketch the walls, or paste corner coordinates.
   - **✏️ Draw walls** works like a CAD sketch. The cursor snaps to corners (□), wall midpoints (△), horizontal, vertical and 45° lines, and lines up with other corners (dashed blue guides). Otherwise it snaps to a 3" grid. A live preview shows the length and angle of the wall you're drawing.
   - **Typing a length**: while drawing, type a length (`10`, `10.5`, `10' 6"`, `126"`) and press Enter to place the next corner exactly that far along the preview direction.
   - Backspace removes the last corner. Click the first corner, double-click, right-click or press Enter to finish. Esc cancels. Hold Alt to place a corner without snapping.
   - **📐 Edit walls**: drag corners (with the same snapping), double-click a wall to add a corner, and right-click a corner to delete it. Click a wall's length to type a new one; straight walls stretch the room so square corners stay square.
   - **Fillets**: in Edit walls, click a corner and type a radius, or use *Fillet all corners*.
   - **Curved walls**: in Edit walls, drag the round handle in the middle of a wall sideways, or click it and type how deep the curve is (0 makes it straight again).
   - Fillets and curves carry into the tracker's room map. In the corner list they're written as `x, y, fillet radius, curve depth`.
3. **Library** — drag pieces onto the plan:
   - *Workbenches & tool chests* — steel workbenches, Husky 72" 11-drawer, tool chest, rolling cart
   - *Cabinets & shelving* — flammable cabinets (17/30/45 gal), storage & wall cabinets, drawer cabinet, wire shelving, bin rack
   - *Office furniture*: 36" storage tower (2-door cabinet over 4 lateral drawers), 6-door locker cabinet (3 wide × 2 tall), 72" credenza (4 doors, stone top), 72" desk with 4 drawers and a cabinet, mobile pedestal (box and file drawer)
   - *Machines* — Prusa MK4 (enclosure), Bambu X1C, Form 4, Form Wash/Cure V2, Glowforge Pro HD, desktop CNC, Hakko FX-951, monitor, PC
   - *Room fixtures* — sink + eyewash, fire extinguisher, eyewash station, first aid, trash can, door
   
   Drop a machine or fixture **on** a bench/wall group to put it on top; drop it on the floor to give it its own spot. Machines bring their consumable slots with them (spool, resin tank + cartridge, IPA, Glowforge material). On a phone, tap a library item to add it to the middle of the room.
   - **🪚 Design a piece**: opens the furniture designer, where you build the front of a piece from cells.
     - **Layout**: start from a box, 4 drawers, 2 doors or a desk. Then split cells into columns or rows, merge them, or drag the divider between them (snaps to ¼"). Each cell gets a name and a type: drawer, deep drawer, cabinet/door or shelf.
     - **Size and finish**: set the footprint, the front size and a finish (maple, oak, black, steel…).
     - **Saving**: *Save to My pieces* adds it to the library. *Apply to selected unit* replaces the layout of a unit on the plan; drawers you didn't delete keep their tracker data.
     - **Import SVG**: bring in a front-elevation drawing from Inkscape, Illustrator or any CAD export. Every rectangle becomes a cell; handle shapes inside cells are ignored. Cells are named from the shape's `<title>`, label or id, or the text drawn inside it. Real sizes are kept when the SVG's width is in in/mm/cm. Gaps under ¾" between cells are closed so neighbouring cells share edges.
     - **Appearance**: pick colours for the body, drawer fronts, handles, top and labels, or click a swatch (Shift-click a swatch to colour the body instead). You can also choose:
       - handle style: bar, knob, cup, edge pull or none
       - texture: flat, wood grain or brushed metal
       - base: none, plinth, legs or casters
       - corner rounding, and the gap between drawer fronts
       Choosing a finish resets the colours to match it. The colours carry into the tracker's front view of the piece.
     - **⬇ SVG / ⬇ PNG / Copy SVG**: export the generated artwork at real size in inches. The SVG imports back into the designer with the same layout, since decoration is marked and skipped on import.
     - Any storage unit on the plan can be opened in the designer with *🪚 Edit layout in designer*.
4. **Click a piece** to rename it, set its tab label, move/resize/rotate it, change its front size, pick a drawer/shelf layout (or set how many), rename each drawer, toggle worktop and under-space storage, reorder or remove machines, or stack a printer ×2.
5. **📦 Inventory** to start using it.
6. Optional: **⬇ Export tracker HTML** saves the current room as `<room-name>-tracker.html`, a single file that works offline on any phone or computer.

*Export layout JSON* / *Import layout JSON* keep the full layout as a `.lablayout.json` file so you can edit it later. The app also autosaves in your browser. *Load example* opens the HatchBridge lab.

The builder warns you if anything sits outside the walls or overlaps.

**Editing tools**
- **Undo / redo**: the toolbar buttons, or Ctrl+Z and Ctrl+Shift+Z (Ctrl+Y also redoes).
- **Multi-select**: Shift-click pieces, drag a box on empty floor, or press Ctrl+A. Drag any selected piece to move the whole group. The side panel then shows *Align* buttons (left, right, top, bottom).
- **Snapping**: pieces snap to straight walls within about 5 inches. Hold Alt while dragging to turn it off. Arrow keys nudge by 3 inches, Shift+arrow by 1 foot.
- **Measurements**: the selected piece shows its size and its distance to the nearest wall on each side.
- **🖨 Print plan**: prints the floor plan with the room name and date.
- **★ Save as piece**: in a unit's panel, saves it (drawers, drawer names and machines on top) to *My pieces* in the library so you can reuse it. Your pieces are kept in this browser and inside saved project files. Click ✕ twice to remove one.

### Equipment library (separate and appendable)

The library has two tabs. **Furniture** holds benches, cabinets and office pieces. **Equipment** has 108 items drawn to scale: 3D printers, paper printers, desk and computer gear, electronics bench instruments, shop tools, and lab equipment. A search box looks across both tabs.

- Equipment lives in [library/equipment.json](library/equipment.json). To add something, add an item `{"k", "n", "w", "h", "fp"}` (front width/height in inches, footprint in feet) and run `python build.py`. Every `library/*.json` file is bundled, and each file gets its own tab.
- Without rebuilding, click **📚 Add a library file** in the builder. The file is kept in that browser.

### Let an AI lay out the room

Click **🤖 AI layout → Copy prompt** and paste it into Claude, ChatGPT or another chatbot along with a description of your room. Then paste the reply back and click **Build it**. If the reply has mistakes, **Copy fix-up request** writes a message listing the errors for you to send back to the bot.

Agents can also open `builder.html#layout=<base64url JSON>` or call `window.LabLayout.importSpec(…)` / `exportSpec()`. **Copy spec** exports the current room so a bot can edit it, and cell ids are kept so inventory survives the round trip. The format is in [docs/AI_LAYOUT_GUIDE.md](docs/AI_LAYOUT_GUIDE.md), with a summary in [llms.txt](llms.txt).

## The tracker it generates

Everything from the HatchBridge tracker, laid out for your room: room-map and per-unit tabs, to-scale front views, drag-and-drop with stacks handing out one at a time, search, quantities, consumable levels, machine slots, checkout, damage and used-up reporting, an activity log with a usage summary, and protected deletes.

**Re-exporting keeps data.** Tracker data is stored in each browser under the room name. If you re-export after changing the layout, items in drawers that still exist stay put, and items from removed drawers land in *Unsorted*.

**Data is per browser unless you turn on sync.** Without sync, each phone or computer keeps its own copy.

**Tracker extras**
- **💾 Backup / 📂 Restore**: download all tracker data as a `.json` file, and load it back later or on another device. Restoring a backup from a different room puts items whose drawers don't exist into *Unsorted*.
- **🛒 Reorder**: give any item a reorder point (tap it 3× to edit). Set a quantity (*Reorder at qty ≤*), or for consumables an amount left (*…or amount left ≤ %*). Low items get a 🛒 badge and appear on the *Reorder* tab, which can download a shopping list as CSV.
- **👥 People**: a list of names that the tracker suggests for *Your name* and for check-outs. Your name is saved per device and is never synced.
- **Due dates**: check-outs default to a due date a week out. Past-due items are marked *OVERDUE*, and the tab shows a ⚠ count. *Group by person* shows who has what.

## Shared inventory (sync)

Trackers can share one inventory across every device through a free [Supabase](https://supabase.com) project.

1. Create a Supabase project. In the **SQL editor**, run:

   ```sql
   create table public.lablayout_rooms (
     id text primary key,
     rev bigint not null default 0,
     data jsonb not null,
     updated_at timestamptz not null default now()
   );
   alter table public.lablayout_rooms enable row level security;
   create policy "lablayout anon read/write" on public.lablayout_rooms
     for all to anon using (true) with check (true);
   ```

2. Copy the **Project URL** and the **anon public key** from *Project Settings → API*.
3. Choose one way to connect:
   - **In the builder**: open *☁ Shared inventory* and paste them in. Every tracker you export is then connected out of the box.
   - **In a tracker**: tap *☁ Sync* and paste them in, on each device.

The same **Room ID** means the same inventory. The first device to connect uploads its data. Any device that joins later takes the shared copy and replaces what it had.

How it works: the tracker saves changes about 1 second after each edit and checks for others' changes every 15 seconds, and again when you return to the tab. If two people edit at once, both people's activity-log entries are kept, and the last save wins for everything else. If the tracker is offline, changes stay on the device and sync once it reconnects.

**Security note:** anyone who has the anon key can read and change the inventory. An exported tracker with sync built in contains that key, so share the file only with people who should edit the inventory.

## Hosting on a website

`dist/` is a ready-to-upload static site: a landing page, the builder, an example tracker and `llms.txt`. To put it on a site, upload the folder or embed the builder in an iframe. See [docs/WEBSITE.md](docs/WEBSITE.md).

## Tests

```
pip install playwright && python -m playwright install chromium
python build.py && python tests/smoke_test.py
```

The smoke test runs the builder and the generated tracker in headless Chromium. It checks export, undo/redo, multi-select, custom pieces, re-export keeping data, backup/restore, reorder, overdue check-outs, and two-device sync against a fake Supabase.

## Rebuilding

After editing anything in `src/`:

```
python build.py
```

## Roadmap

- Windows `.exe` (Electron wrapper around the exported tracker)
- QR labels per drawer that open the tracker straight to it
- Safety and compliance fields (SDS links, inspection dates, flammable cabinet capacity)
