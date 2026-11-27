# LabLayout features

LabLayout is one HTML file (`site/builder.html`) that lays out labs and tool cribs, tracks their inventory and books furniture for events. It works offline, needs no install, and runs in feet and inches or in metres.

## Modes

- **✏️ Edit layout**: draw rooms and walls, then arrange the furniture.
- **📦 Inventory**: the room's tracker, for checking items in and out, consumables, a reorder list and an activity log.
- **📅 Events**: book furniture for calendar events (see [Events](#events)).

## Walls and rooms

- **Room shape**: a rectangle from width and depth, drawn wall by wall, or typed as a list of corners. Corners can have fillets and arcs.
- **Wall drawing snaps**: to corners, wall midpoints, horizontal, vertical and 45° lines, and to other corners (shown as blue guides). You can type a length while drawing.
- **Snapping on and off**: the Snap button switches snapping off; holding Alt skips it for a single drag.
- **Corner labels**: click a wall to see its corners labelled, then click a corner to type exact coordinates.
- **Square up** straightens nearly horizontal or vertical walls.
- **Wall width**: walls have a real thickness, drawn outside the room so the room keeps its size.
- **Interior walls** are library pieces (Interior wall 8 ft).
- **Grid**: the grid size can be changed, and furniture snaps to it.
- **Hover coordinates**: moving the mouse over the plan shows the grid position in the bottom-right corner.

## Rooms and areas inside a floor

- **Automatic rooms**: spaces enclosed by walls become rooms on their own. Their names and settings survive when walls move.
- **Room tools**:
  - **Draw room**: click corners; snaps to walls first, then the grid.
  - **Drag a box**: drag a rectangle on the plan.
  - **Click a space**: fills an enclosed space as a room.
- **Fit rooms to walls** pulls room edges onto the walls' inner faces.
- **Room corners**: rooms show their corners when clicked, and you can edit them by typing. Rooms have a corners list and square up like walls do.
- **Room edges snap** to other rooms.
- **Room labels**: rooms show just their name (plus ↗ or › when they open another room); colour shows who a room belongs to. Labels shrink to fit their room and are hidden when they can't fit. In a layout that contains a room, that room's furniture labels are hidden (hover or select a piece to see its name) and show normally inside the room itself.
- **One room per piece**: each piece belongs to the room its centre is in. A piece that hangs over into another room is nudged fully inside its own. Anchored pieces are left alone. A piece still in two rooms (anchored, or too big to fit) is listed in the checks with both room names, and a message appears when you drop it there.

## Doors

- **Doors only go in walls**, outer or interior, and fill the wall's thickness.
- **Doors stay clear of corners.**
- **Door types**: swing, double and sliding.
- **Shared doors**: a door between two rooms shows in both, on the same wall and facing the same way.

## Nested layouts

- **Rooms within layouts**: a room area on a floor plan can open its own room, and layouts can nest inside larger layouts.
- **Navigation**:
  - **In Inventory**: click a room to go into it; click outside it to go back up.
  - **Breadcrumbs**: show where you are and jump back to any level.
- **Linked rooms take their walls from the parent layout**, so they can't be edited separately.
- **Furniture appears at every level**: a linked room's furniture shows in the parent layout and can be edited from either view. A piece belongs to whichever room its centre sits in.

## Furniture and the library

- **Library**: drag pieces onto the plan, or tap one on a phone. The library is searchable and has category tabs.
- **Piece designer**: design drawers, doors and shelves, or import an SVG front elevation.
- **Library packs**: add library files (`.json`).
- **Editing pieces**: select, multi-select, rotate, duplicate, group, anchor, nudge with the arrow keys, measure, and copy and paste between rooms.
- **Checks**: the app flags pieces outside the walls or overlapping each other.
- **Undo and redo.**

## Events

- **Creating events**: give each event a name, a start, an end and notes. Events are saved with the room.
- **Booking furniture**: pick an event, then click pieces on the plan to book or release them.
- **Any date and time**: events run on any date, from any start time to any end time, including ones that span several days.
- **Import a calendar**: **📥 Import calendar (.ics)** brings in events from Google Calendar, Outlook, Apple Calendar or any .ics file. Time zones and durations are read. Importing the same file again updates those events instead of duplicating them. For repeating events, only the first occurrence comes in, and its notes say so.
- **Event layouts**: each event can have its own furniture arrangement. In Events mode, drag unanchored pieces to set them up for that event. Anchored pieces can be booked with a click but never moved. The room's own layout doesn't change, and **Reset to room layout** puts the event back.
- **Layout presets per room**: save an event's arrangement as a named preset (for example Class or Party). Other events in the same room can start from it with **Start from**, and changes made for one event don't alter the preset. Each room keeps its own presets, listed in the Events panel.
- **Upcoming events on each piece**: in Edit layout, selecting a piece lists the upcoming events it's booked for, with a button to open each one in Events mode.
- **Colours on the plan**:
  - Orange: booked for this event.
  - Red: also booked by another event at the same time (a clash).
  - Dashed grey: busy with another event at the same time.
- **Clash warnings**: a clash raises a warning and is marked in the event list and the furniture list.
- **Event list**: shows upcoming or all events, plus how many pieces each one has booked.
- **Event actions**: duplicate an event, delete it, release everything at once, or download it as an `.ics` file for Google Calendar, Outlook or Apple Calendar. The `.ics` file lists the booked pieces.

## Inventory (tracker)

- **Tracking**: check items in and out, track consumables, keep a reorder list and an activity log.
- **Movable storage**: any single item, such as a footlocker, tool chest, toolbox or camera bag, can be made a container with **🧰 Make container**. Containers hold items, and they can also go inside other containers. A container counts as an item itself. Checking it out takes everything inside with it, and returning it brings it back with its contents. The search and the checked-out list show where things are, for example "🧰 Camera bag in Workbench 1 › Worktop" or "🧰 Camera bag (checked out)".
- **Layout changes keep inventory**: when the layout changes, drawers you keep keep their items, and items from deleted drawers move to *Unsorted*.
- **Exporting**: export a standalone tracker HTML file for any room.
- **Shared inventory** (optional): a Supabase connection lets several devices share one inventory.

## Files and sharing

- **Projects**: a project can hold several rooms, shown as tabs. You can add, copy and rename them.
- **File formats**: Layout JSON holds every room; Room JSON holds one. Both can be exported and imported.
- **Password-locked layouts**: a layout can be encrypted with a password (AES-GCM, key from PBKDF2). Entering the password on the home page opens it.
- **AI layout**: generates a layout from AI layout specs (see `site/AI_LAYOUT_GUIDE.md` and `site/llms.txt`).
- **Print plan.**

## Display

- **Units**: feet and inches, or metres and centimetres. You can type `2.4 m`, `240 cm` or `2400 mm` in either mode.
- **Colour-blind palette** (Okabe-Ito).
- **Phones**: the layout works at phone width.
- **Hosting**: deployed as a static site on Vercel (`vercel.json` serves `site/`).
