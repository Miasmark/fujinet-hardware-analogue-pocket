#!/usr/bin/env python3
"""Refresh tools/symcache.sexpr: the flattened stock KiCad symbols gen_sch.py
embeds in the sheets, so the generator never depends on another project.

Two sources:
  * this file's own cache, first taken from FujiNet-7800-Rev0's (stock symbols
    as flattened by eeschema) -- KEEP names the ones this board shares with it
    (the FujiNet half, the passives, the power path);
  * the installed KiCad symbol libraries (/usr/share/kicad/symbols), for the
    parts new to this board.  Derived symbols ("extends") are flattened the
    way eeschema does it: the parent's units and drawings under the derived
    name, the derived symbol's own properties on top.

Usage: python3 tools/harvest_symbols.py        (rewrites tools/symcache.sexpr)
"""
import copy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexpr import parse, dump, find, findall, Q

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'symcache.sexpr')
KICAD_SYMS = os.environ.get('KICAD_SYMBOL_DIR', '/usr/share/kicad/symbols')

# lib -> symbols to flatten from the stock libraries
STOCK = {
    'Battery_Management': ['MCP73831-2-OT'],      # LiPo charger
    'Regulator_Switching': ['TPS63001'],          # 3.3 V buck-boost
    '74xGxx': ['74LVC1G34'],                      # link buffers
    'Connector_Generic': ['Conn_01x02'],          # the cell
    'power': ['+BATT', '+VSW'],                   # VBAT, VSYS
}
# symbols of the 7800 board's cache this board keeps
KEEP = {'Connector:TestPoint', 'Connector:USB_C_Receptacle_USB2.0_16P', 'Device:C', 'Device:L', 'Device:LED',
        'Device:R', 'Device:R_Pack04', 'Diode:BAT54C', 'Diode:ESD5Zxx', 'Diode:SS34',
        'Interface_USB:CP2102N-Axx-xQFN28', 'RF_Module:ESP32-S3-WROOM-1', 'Switch:SW_Push',
        'Transistor_BJT:UMH3N', 'Transistor_FET:AO3401A', 'power:+3V3', 'power:GND', 'power:PWR_FLAG',
        'power:VBUS'}


def flatten(lib, name, syms):
    s = syms[name]
    ext = find(s, 'extends')
    if not ext:
        out = copy.deepcopy(s)
    else:
        out = flatten(lib, str(ext[1]), syms)
        parent = out[1].split(':', 1)[1]
        # the derived symbol's properties replace the parent's of the same name
        mine = {str(p[1]): p for p in findall(s, 'property')}
        for i, e in enumerate(out):
            if isinstance(e, list) and e and e[0] == 'property' and str(e[1]) in mine:
                out[i] = copy.deepcopy(mine.pop(str(e[1])))
        first_sub = next(i for i, e in enumerate(out) if isinstance(e, list) and e and e[0] == 'symbol')
        for p in mine.values():
            out.insert(first_sub, copy.deepcopy(p)); first_sub += 1
        for sub in findall(out, 'symbol'):
            sub[1] = Q(name + str(sub[1])[len(parent):])
    out[1] = Q(lib + ':' + name)
    return out


def main():
    got = {}
    for s in parse(open(CACHE).read())[1:]:
        if s[1] in KEEP:
            got[s[1]] = s
    for lib, names in STOCK.items():
        t = parse(open(os.path.join(KICAD_SYMS, lib + '.kicad_sym')).read())
        syms = {str(s[1]): s for s in t[1:] if isinstance(s, list) and s[0] == 'symbol'}
        for n in names:
            f = flatten(lib, n, syms)
            got[f[1]] = f
    out = ['symcache'] + [got[k] for k in sorted(got)]
    open(CACHE, 'w').write(dump(out) + '\n')
    print('\n'.join(sorted(got)))


if __name__ == '__main__':
    main()
