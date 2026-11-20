#!/usr/bin/env python3
"""Write the project footprints that are not stock KiCad ones (besides the slot edge,
make_edge_fp.py):

LiPo_Landing_30x40 -- the battery's landing pad on the back (B side) of the upper board: the
  outline of a 1S LiPo pouch up to 30 x 40 mm (a 403040 / 503040, about 400-600 mAh, with its
  protection board inside that size) on B.SilkS and B.Fab, with corner marks; two hand-solder
  pads on B.Cu for the cell's leads at its +x end (pad 1 +, pad 2 -), marked on the silk.  The
  footprint carries no part to place (no paste, not in the position file); the cell is stuck
  down with double-sided foam tape inside the outline and its leads soldered to the pads.
  Origin: the cell's centre.  A front-side footprint whose copper and graphics are all on the
  back, so the board stays single-sided for assembly.  No courtyard: gen_pcb.py puts a B.Cu rule
  area over the cell (no footprints on the back there) instead, since the USB-C's shell legs and
  the microSD's locating pegs pass through the board near and under it.

Usage: python3 tools/make_fp_extra.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, '..', 'FujiNet-Pocket.pretty')

CELL_W, CELL_H = 40.0, 30.0       # the landing outline (cell length along x, width along y)
MARGIN = 0.5                      # silk outside the cell
PAD_X = CELL_W / 2 + 2.6          # lead pads beside the cell's +x end
PAD_DY = 3.0
PAD_W, PAD_H = 3.0, 2.4


def F(size=1.0, mirror=False):
    j = ' (justify mirror)' if mirror else ''
    return '(effects (font (size %g %g) (thickness %g))%s)' % (size, size, size * 0.15, j)


def line(a, b, layer, w=0.12):
    return '\t(fp_line (start %g %g) (end %g %g) (stroke (width %g) (type solid)) (layer "%s"))' % (
        a[0], a[1], b[0], b[1], w, layer)


def rect(x0, y0, x1, y1, layer, w=0.1):
    return '\t(fp_rect (start %g %g) (end %g %g) (stroke (width %g) (type solid)) (fill no) (layer "%s"))' % (
        x0, y0, x1, y1, w, layer)


def landing():
    hw, hh = CELL_W / 2, CELL_H / 2
    sw, sh = hw + MARGIN, hh + MARGIN
    out = ['(footprint "LiPo_Landing_30x40"', '\t(version 20241229)', '\t(generator "fujinet_gen")',
           '\t(layer "F.Cu")',
           '\t(descr "Landing pad on the back for a 1S LiPo pouch up to 30 x 40 mm (403040 / 503040): outline, '
           'corner marks, lead pads 1 (+) and 2 (-) on B.Cu at the cell\'s +x end; no part placed")',
           '\t(tags "lipo battery cell landing pad")',
           '\t(property "Reference" "REF**" (at %g %g 0) (layer "B.SilkS") %s)' % (-hw + 4, -hh + 2.5, F(1.0, True)),
           '\t(property "Value" "LiPo 30x40" (at 0 0 0) (layer "B.Fab") %s)' % F(1.5, True),
           '\t(attr smd exclude_from_pos_files exclude_from_bom)',
           rect(-hw, -hh, hw, hh, 'B.Fab'),
           '\t(fp_text user "1S LiPo, protected, <= 30 x 40 x 5 mm" (at 0 2.5 0) (layer "B.Fab") %s)' % F(1.0, True),
           '\t(fp_text user "foam tape inside the outline" (at 0 4.5 0) (layer "B.Fab") %s)' % F(1.0, True)]
    # corner marks (L shapes) and a dashed-looking outline: four sides, gaps at the middles
    L = 4.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = (sx * sw, sy * sh)
            out.append(line(c, (c[0] - sx * L, c[1]), 'B.SilkS', 0.2))
            out.append(line(c, (c[0], c[1] - sy * L), 'B.SilkS', 0.2))
    for sy in (-1, 1):
        out.append(line((-sw + L + 2, sy * sh), (-2, sy * sh), 'B.SilkS'))
        out.append(line((2, sy * sh), (sw - L - 2, sy * sh), 'B.SilkS'))
    for sx in (-1, 1):
        out.append(line((sx * sw, -sh + L + 2), (sx * sw, sh - L - 2), 'B.SilkS'))
    # lead pads, + and - on the silk beside them
    for num, dy, mark in (('1', -PAD_DY, '+'), ('2', PAD_DY, '-')):
        out.append('\t(pad "%s" smd rect (at %g %g) (size %g %g) (layers "B.Cu" "B.Mask"))'
                   % (num, PAD_X, dy, PAD_W, PAD_H))
        out.append('\t(fp_text user "%s" (at %g %g 0) (layer "B.SilkS") %s)' % (mark, PAD_X + PAD_W / 2 + 1.3, dy, F(1.5, True)))
    out.append(')')
    return '\n'.join(out) + '\n'


def main():
    fn = os.path.join(LIB, 'LiPo_Landing_30x40.kicad_mod')
    open(fn, 'w').write(landing())
    print(os.path.relpath(fn))


if __name__ == '__main__':
    main()
