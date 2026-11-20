# Shell notes (draft)

No shell is designed yet. This is what the board gives a shell, molded or printed, and the limits
it has to respect.

## Inputs

All of these are generated: run `tools/gen_pcb.py`, then `tools/export_fab.py`.

| File | What |
|---|---|
| `case/board-anchors.json`, `case/board-anchors.scad` | Board outline, thickness, the six holes, the cell's outline on the back, the USB-C and microSD mouths, buttons, LEDs, antenna, and the slot line. KiCad frame: mm, y down, front = the component side. |
| `exports/FujiNet-Pocket-Rev0.step` | The board with every part and a 40 x 30 x 4 mm stand-in for the cell, for the CAD the shell is drawn in. |

## The board in the shell

- **Board:** 51.4 x 82 mm, 1.0 mm thick.
  - Bottom 8.6 mm: the Game Boy-style tab, 49.2 mm wide, with the 32 fingers.
  - About 31 mm, measured from the insertion edge, goes into the Pocket's slot (`slot_y`). This
    is an **estimate**: measure it on a Pocket. Above that line the board stands clear of the
    Pocket.
- **Front, above the slot line:** every part, 3.3 mm at most (ESP32-S3 module 3.1 mm, USB-C 3.2
  mm).
- **Front, inside the slot:** only the link buffers (SOT-23-5, 1.45 mm), 0603s and flat test pads.
- **Back:** only the cell, up to 30 x 40 x 5 mm, and its two lead pads, on the landing outline.
  Nothing else is placed on the back.
- **Thickness above the slot:** about 3.3 (front) + 1.0 (board) + 5.5 (cell and tape) = 9.8 mm,
  plus the walls. Inside the slot the shell must keep to a GB cartridge's profile.

## Must

1. **Voltage switch:** the lower corner over the Pocket's voltage switch must be **GBA-shaped**,
   so the switch is never pressed and the slot stays at 3.3 V. A GB/GBC corner puts the slot at
   5 V. Cut it 0.5-1 mm deeper and wider than a GBA cart's. Print a blank first and check that it
   seats fully and clears the switch.
2. **Antenna:** keep the top 7 mm (the module's antenna, flush with the top edge) under plastic
   only: no metal, no screws, no ink or paint with metal in it, and a thin wall.
3. **Openings:**
   - USB-C, west side, plug in from the west;
   - microSD, east side, card in from the east;
   - the two buttons (S3 reset, S3 BOOT), by plungers or pin holes;
   - the three LEDs on the west edge (WiFi, bus, charge), by light pipes or thin windows.
4. **Holes:** six M2 holes (2.2 mm), with 3 mm around each kept free of parts on the front:
   - two below the antenna band;
   - two just above the slot line;
   - two inside the slot.

   Use them for screws into heat-set inserts, or for locating pins when molding around the board.
5. **The cell is not potted or glued in hard:** LiPo pouches swell with age. Leave about 0.5 mm
   over it, and hold it with foam tape on the landing outline.

## Watch

- **The microSD's two locating pegs** pass through the board under the cell's outline. Check that
  they do not stand proud of the back, or keep the tape thick enough to bridge them.
- **The USB-C's four shell legs** are soldered through the board beside the cell's lead pads.
  They stand about 1 mm proud of the back, outside the cell's outline.
- **Shoulder buttons:** the shell is no wider than a GB cartridge (57 mm) where it stands
  between them.
