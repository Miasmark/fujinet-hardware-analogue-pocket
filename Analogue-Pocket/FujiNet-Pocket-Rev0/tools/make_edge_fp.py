#!/usr/bin/env python3
"""Write FujiNet-Pocket.pretty/Pocket_Cart_Edge_32.kicad_mod: the Game Boy / GBA cartridge edge
the Analogue Pocket's slot takes.

Geometry: Gekkio's GB-CART32K-A (github.com/Gekkio/gb-hardware, CC-BY-4.0), footprint
Gekkio_Connector_PCBEdge:GameBoy_Cartridge_1x32_P1.50mm_Edge, read from that board file
(2026-11-20) and re-drawn here, not copied:
  * 32 fingers at 1.5 mm, all on one face (F.Cu here, the component side);
  * pins 2-31: 1.0 x 5.5 mm, ending 1.5 mm from the insertion edge;
  * pins 1 (VCC) and 32 (GND): 1.3 x 6.0 mm at +-23.4, ending 1.0 mm from it, so the rail and
    ground make contact first;
  * the tab: 49.2 mm wide, 8.6 mm deep, 0.9 mm corner radius; the body above it 51.4 mm wide;
  * a 1.0 mm board.
Seen from F.Cu with the fingers down, pin 1 is at the left (-x).  Local frame as Gekkio's: the
insertion edge is at y = +4.0, the board extends in -y.  The board outline itself is the PCB's
(Edge.Cuts, drawn with the layout); this footprint draws the tab on F.Fab only.

UNVERIFIED against a Pocket: check the finger face and pin 1 against a real GB cartridge in the
Pocket (pin 1 is the rail: 3.3 V with a GBA cart) before ordering boards.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'FujiNet-Pocket.pretty', 'Pocket_Cart_Edge_32.kicad_mod')

PITCH = 1.5
EDGE_Y = 4.0                 # insertion edge
TAB_HALF, BODY_HALF = 24.6, 25.7
TAB_TOP = -4.6               # where the tab meets the body
R_CORNER = 0.9


def pin_x(n):
    if n == 1:
        return -23.4
    if n == 32:
        return 23.4
    return round(-21.75 + PITCH * (n - 2), 3)


def pad(n):
    if n in (1, 32):
        w, h, cy = 1.3, 6.0, 0.0
    else:
        w, h, cy = 1.0, 5.5, -0.25
    return ('\t(pad "%d" smd rect (at %s %s) (size %s %s) (layers "F.Cu" "F.Mask"))'
            % (n, pin_x(n), cy, w, h))


def line(a, b, layer, w=0.1):
    return ('\t(fp_line (start %s %s) (end %s %s) (stroke (width %s) (type solid)) (layer "%s"))'
            % (a[0], a[1], b[0], b[1], w, layer))


def arc(s, m, e, layer, w=0.1):
    return ('\t(fp_arc (start %s %s) (mid %s %s) (end %s %s) (stroke (width %s) (type solid)) (layer "%s"))'
            % (s[0], s[1], m[0], m[1], e[0], e[1], w, layer))


def main():
    c = R_CORNER * (1 - 2 ** -0.5)
    out = ['(footprint "Pocket_Cart_Edge_32"',
           '\t(version 20241229)', '\t(generator "fujinet_gen")', '\t(layer "F.Cu")',
           '\t(descr "Analogue Pocket / Game Boy / GBA cartridge edge: 32 fingers at 1.5 mm on one face; '
           'pins 1 and 32 longer; 1.0 mm board (geometry: Gekkio GB-CART32K-A, CC-BY-4.0)")',
           '\t(tags "game boy gba analogue pocket cartridge edge")',
           '\t(property "Reference" "REF**" (at 0 -6.5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
           '\t(property "Value" "Pocket_Cart_Edge_32" (at 0 -8.5 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
           '\t(attr smd exclude_from_pos_files exclude_from_bom)',
           '\t(fp_text user "1" (at -23.4 -4.5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
           '\t(fp_text user "32" (at 23.4 -4.5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))']
    # the tab on F.Fab: body shoulders, sides, rounded corners, the insertion edge
    y_arc = EDGE_Y - R_CORNER
    for s in (-1, 1):
        out.append(line((s * BODY_HALF, TAB_TOP - 2.4), (s * BODY_HALF, TAB_TOP), 'F.Fab'))
        out.append(line((s * BODY_HALF, TAB_TOP), (s * TAB_HALF, TAB_TOP), 'F.Fab'))
        out.append(line((s * TAB_HALF, TAB_TOP), (s * TAB_HALF, y_arc), 'F.Fab'))
        out.append(arc((s * TAB_HALF, y_arc), (round(s * (TAB_HALF - c), 6), round(EDGE_Y - c, 6)),
                       (s * (TAB_HALF - R_CORNER), EDGE_Y), 'F.Fab'))
    out.append(line((-(TAB_HALF - R_CORNER), EDGE_Y), (TAB_HALF - R_CORNER, EDGE_Y), 'F.Fab'))
    out.append('\t(fp_rect (start %s %s) (end %s %s) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))'
               % (-TAB_HALF, -3.5, TAB_HALF, EDGE_Y))
    out += [pad(n) for n in range(1, 33)]
    out.append(')')
    open(OUT, 'w').write('\n'.join(out) + '\n')
    print(os.path.relpath(OUT))


if __name__ == '__main__':
    main()
