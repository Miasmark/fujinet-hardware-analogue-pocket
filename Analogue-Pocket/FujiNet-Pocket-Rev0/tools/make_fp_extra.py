#!/usr/bin/env python3
"""Write the project footprints that are not stock KiCad ones (besides the slot edge,
make_edge_fp.py):

LiPo_Leads -- where the battery's leads land.  The cell (a protected 1S LiPo pouch up to
  30 x 50 x 5 mm, a 403050 / 503050) rides over the components on a shelf in the shell, on the
  component side, which faces the open side of the Pocket's cartridge recess (the board's flat
  back lies against the Pocket); gen_pcb.py draws its outline (CELL) on F.Fab for the shell.  Its
  leads, from the protection board at its lower end, come down to these two hand-solder pads:
  pad 1 (+) at +x, pad 2 (-) at -x, 6 mm apart, marked on the silk.  No part to place (no paste,
  not in the position file, not on the BOM).  Origin: between the pads.

Usage: python3 tools/make_fp_extra.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, '..', 'FujiNet-Pocket.pretty')

PAD_DX = 3.0                      # pads at +-3 mm
PAD_W, PAD_H = 3.0, 2.4


def F(size=1.0):
    return '(effects (font (size %g %g) (thickness %g)))' % (size, size, size * 0.15)


def leads():
    out = ['(footprint "LiPo_Leads"', '\t(version 20241229)', '\t(generator "fujinet_gen")', '\t(layer "F.Cu")',
           '\t(descr "Hand-solder pads for a 1S LiPo\'s leads: 1 (+) at +x, 2 (-) at -x; the cell rides on a shelf '
           'in the shell over the components (gen_pcb.CELL); no part placed")',
           '\t(tags "lipo battery leads solder pads")',
           '\t(property "Reference" "REF**" (at 0 %g 0) (layer "F.SilkS") %s)' % (-(PAD_H / 2 + 1.2), F(0.8)),
           '\t(property "Value" "LiPo" (at 0 %g 0) (layer "F.Fab") %s)' % (PAD_H / 2 + 1.2, F(0.8)),
           '\t(attr smd exclude_from_pos_files exclude_from_bom)']
    for num, dx, mark in (('1', PAD_DX, '+'), ('2', -PAD_DX, '-')):
        out.append('\t(pad "%s" smd rect (at %g 0) (size %g %g) (layers "F.Cu" "F.Mask"))' % (num, dx, PAD_W, PAD_H))
        out.append('\t(fp_text user "%s" (at %g 0 0) (layer "F.SilkS") %s)'
                   % (mark, dx + (1 if dx > 0 else -1) * (PAD_W / 2 + 1.0), F(1.5)))
    x = PAD_DX + PAD_W / 2 + 2.0
    out.append('\t(fp_rect (start %g %g) (end %g %g) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))'
               % (-x, -(PAD_H / 2 + 0.3), x, PAD_H / 2 + 0.3))
    out.append(')')
    return '\n'.join(out) + '\n'


def main():
    fn = os.path.join(LIB, 'LiPo_Leads.kicad_mod')
    open(fn, 'w').write(leads())
    print(os.path.relpath(fn))


if __name__ == '__main__':
    main()
