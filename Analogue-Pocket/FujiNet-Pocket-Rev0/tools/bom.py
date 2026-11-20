#!/usr/bin/env python3
"""Write FujiNet-Pocket-Rev0-BOM.csv from design.py: one line per value + footprint + MPN, with the
references, quantity, manufacturer and LCSC code (empty where none is chosen yet).  Parts with
bom=False (the slot edge, test pads) are left out.

Usage: python3 tools/bom.py
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', D.PROJECT + '-BOM.csv')


def natural(ref):
    i = len(ref.rstrip('0123456789'))
    return (ref[:i], int(ref[i:]))


def main():
    groups = {}
    for p in D.PARTS:
        if not p.bom:
            continue
        k = (p.value, p.footprint.split(':')[1], p.mpn)
        groups.setdefault(k, []).append(p)
    rows = []
    for (value, fp, mpn), ps in groups.items():
        refs = sorted((p.ref for p in ps), key=natural)
        rows.append([' '.join(refs), len(ps), value, fp, ps[0].mfr, mpn, ps[0].lcsc,
                     'DNP' if all(p.dnp for p in ps) else '', ps[0].desc])
    rows.sort(key=lambda r: natural(r[0].split()[0]))
    with open(OUT, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['References', 'Qty', 'Value', 'Footprint', 'Manufacturer', 'MPN', 'LCSC', 'DNP', 'Description'])
        w.writerows(rows)
    missing = [r[5] for r in rows if not r[6]]
    print('%s: %d lines, %d parts; no LCSC code yet: %s' % (os.path.basename(OUT), len(rows),
                                                           sum(r[1] for r in rows), ', '.join(missing) or 'none'))


if __name__ == '__main__':
    main()
