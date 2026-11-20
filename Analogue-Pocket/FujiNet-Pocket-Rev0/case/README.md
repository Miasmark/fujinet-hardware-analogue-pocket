# Shell notes (draft)

No shell is designed yet. This is what the board gives a shell, molded or printed, and the limits
it has to respect.

## Inputs

All of these are generated: run `tools/gen_pcb.py`, then `tools/export_fab.py`.

| File | What |
|---|---|
| `case/board-anchors.json`, `case/board-anchors.scad` | Board outline, thickness, the six holes, the cell's place on its shelf (`cell`, `shelf_z`) and its lead pads, the USB-C and microSD mouths, buttons, LEDs, antenna, and the recess lines (`slot_y`, `lip_y`). KiCad frame: mm, y down, front = the component side. |
| `exports/FujiNet-Pocket-Rev0.step` | The board with every part and a 30 x 50 x 4 mm stand-in for the cell at shelf height, for the CAD the shell is drawn in. |

## The board in the Pocket

- **Board:** 51.4 x 82 mm, 1.0 mm thick.
  - Bottom 8.6 mm: the Game Boy-style tab, 49.2 mm wide, with the 32 fingers.
  - About 31 mm, measured from the insertion edge, goes into the Pocket's cartridge recess
    (`slot_y`). This is an **estimate**: measure it on a Pocket.
- **Back** (the flat side): in the recess it lies nearly flush against the Pocket.
  - Nothing is placed on the back anywhere. The shell has no wall there inside the recess, or only
    a thin skin if the fit allows.
  - Above the recess, the USB-C's four shell legs and the microSD's two locating pegs come
    through the back, about 1 mm proud.
- **Front** (the component side, the fingers' side): in the recess it faces the open side.
  - The Pocket's lip covers it below about 15 mm from the insertion edge (`lip_y`, an
    **estimate**). Only low parts go there: SOT-23-5 (1.45 mm), 0603s, flat pads.
  - Above `lip_y` the front is open. The parts are 3.3 mm at most (ESP32-S3 module 3.1 mm, USB-C
    3.2 mm).

## The battery shelf

- The cell (a protected 1S LiPo up to 30 x 50 x 5 mm, e.g. a 403050 or 503050) rides over the
  components on a shelf in the shell.
  - It lies over the board at `cell` (x 88..118, y 79..129).
  - The shelf's top face is `shelf_z` = 4.4 mm above the board: the tallest parts under it plus
    0.4 mm clearance, plus a 0.8 mm shelf.
  - It is clear of the antenna band (the top 7 mm) and of the two buttons.
- Its leads come down from its lower end, where a pouch's protection board is, to the two pads at
  `cell_leads`, just above the lip: `+` 3 mm east, `-` 3 mm west. Leave a channel for them.
- **Thickness:** from the board's back, about 1.0 (board) + 4.4 (shelf) + 5.0 (cell) + 0.5
  (swelling room) + the front wall, about 11-12 mm over the cell.
  - Below `lip_y` the shell keeps to a GB cartridge's profile.
- **Hold the cell, don't pot it:** LiPo pouches swell with age. Use foam tape on the shelf and
  about 0.5 mm of room over the cell. The shelf must not press on the parts under it.

## Must

1. **Voltage switch:** the lower corner over the Pocket's voltage switch must be **GBA-shaped**,
   so the switch is never pressed and the slot stays at 3.3 V. A GB/GBC corner puts the slot at
   5 V. Cut it 0.5-1 mm deeper and wider than a GBA cart's. On that side the board keeps the
   tab's width for 10 mm above the tab base (`switch_notch`, an estimate), so the corner has
   room. Print a
   blank first and check that it seats fully and clears the switch.
2. **Antenna:** keep the top 7 mm (the module's antenna, flush with the top edge) under plastic
   only: no metal, no screws, no ink or paint with metal in it, and a thin wall. The cell stops
   below it.
3. **Openings:**
   - USB-C, west side, plug in from the west;
   - microSD, east side, card in from the east, under the shelf's edge;
   - the two buttons (S3 reset, S3 BOOT), by plungers or pin holes, west of the shelf;
   - the three LEDs on the west edge (WiFi, bus, charge), by light pipes or thin windows.
4. **Holes:** six M2 holes (2.2 mm), with 3 mm around each kept free of parts:
   - two below the antenna band;
   - two just above `slot_y`;
   - two inside the recess.

   Use them for screws into heat-set inserts, or for locating pins when molding around the board.
   The shelf can stand on bosses over them. Inside the recess the back has no room for screw
   heads: use them from the front there, or as pins.

## Watch

- **The back in the recess** must slide against the Pocket without catching.
- **Shoulder buttons:** the shell is no wider than a GB cartridge (57 mm) where it stands
  between them.
