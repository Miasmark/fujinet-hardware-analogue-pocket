#!/usr/bin/env python3
"""Generate FujiNet-Pocket-Rev0.kicad_pcb (placed, unrouted) from design.py.

Board (KiCad frame, mm, y down): the Game Boy / GBA cartridge tab of the Pocket's slot (x 75.4..
124.6, y 141.4..150, y = 150 the insertion edge; make_edge_fp.py has the geometry, from Gekkio's
GB-CART32K-A) under a 51.4 mm wide body (x 74.3..125.7) that runs up to the top edge Y0.  The
Pocket's shell top is about SLOT_Y = 119 (ESTIMATE): below it the board's flat back lies nearly
flush against the Pocket in its cartridge recess, and the component side (the fingers' side) faces
the recess's open side, covered only by the Pocket's lip below about LIP_Y = 135 (ESTIMATE).  The
cell rides over the components on a shelf in the shell (CELL, SHELF_Z), its leads down to two
pads on the component side.  1.0 mm, 4
copper layers:
  F.Cu   signals + GND pour     (every part; the fingers)
  In1    GND plane
  In2    +3V3 plane
  B.Cu   signals + GND pour     (no parts: it lies against the Pocket)
The ESP32-S3 antenna sits flush with the top edge over the module footprint's own keep-out band
(no copper, holes or parts on any layer, across the board).  Six M2 holes (HOLES) for the shell,
clear of parts by HOLE_KEEP; case/board-anchors.scad and case/board-anchors.json carry them, the
outline, the ports, the buttons, the LEDs and the cell's outline to the shell design.

Carried over from FujiNet-7800-Rev0's gen_pcb.py (fujinet-hardware, CERN-OHL-W-2.0): the
footprint writer, the schematic-netlist binding, the zones and the plane fan-out; the board itself
is this one's.

Usage: python3 tools/gen_pcb.py
"""
import os, sys, math, copy, json, re, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexpr import parse, dump, find, findall, Q
from tmpdir import tmp
import design as D
import gen_sch
import make_edge_fp as EG

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
PCB = os.path.join(PRJ, D.PROJECT + '.kicad_pcb')
K = D.KEY

# ---- geometry (mm, KiCad frame: y down) -----------------------------------
XC = 100.0
X0, X1 = XC - EG.BODY_HALF, XC + EG.BODY_HALF      # body 51.4 wide
TAB_X0, TAB_X1 = XC - EG.TAB_HALF, XC + EG.TAB_HALF  # tab 49.2 wide
EDGE_FP_Y = 146.0               # the edge footprint's origin (its insertion edge at local +4.0)
Y1 = EDGE_FP_Y + EG.EDGE_Y      # 150: insertion edge
TAB_Y = EDGE_FP_Y + EG.TAB_TOP  # 141.4: tab base = bottom of the body
Y0 = 68.0                       # top edge: the antenna
PAD_TOP_Y = EDGE_FP_Y - 3.0     # finger copper starts here
THICKNESS = 1.0
SLOT_Y = 119.0                  # the Pocket's shell top, ESTIMATE (placement.py): the back is flush below
LIP_Y = 135.0                   # the Pocket's lip over the component side, ESTIMATE: low parts below
CH_TOP, CH_SH, CH_TAB = 2.0, 0.6, EG.R_CORNER      # chamfers: top corners, tab shoulders, insertion corners
# the voltage-switch corner: on the left (pin 1's side, seen from the component side with the
# fingers down) the tab's edge runs straight on up NOTCH_H past the tab base before the body steps
# out to its full width, so the shell's GBA-shaped corner there clears the Pocket's voltage switch.
# ESTIMATE -- measure the switch on a Pocket.
NOTCH_H = 10.0
NOTCH = (X0, TAB_Y - NOTCH_H, TAB_X0, TAB_Y)
OUTLINE = [(X0 + CH_TOP, Y0), (X1 - CH_TOP, Y0), (X1, Y0 + CH_TOP),
           (X1, TAB_Y - CH_SH), (X1 - CH_SH, TAB_Y), (TAB_X1, TAB_Y),
           (TAB_X1, Y1 - CH_TAB), (TAB_X1 - CH_TAB, Y1), (TAB_X0 + CH_TAB, Y1), (TAB_X0, Y1 - CH_TAB),
           (TAB_X0, NOTCH[1]), (X0 + CH_SH, NOTCH[1]), (X0, NOTCH[1] - CH_SH), (X0, Y0 + CH_TOP)]
BODY = [(X0, Y0), (X1, Y0), (X1, TAB_Y), (TAB_X0, TAB_Y), (TAB_X0, NOTCH[1]), (X0, NOTCH[1])]   # planes / pours
# M2 holes for the shell (x, y, diameter): two by the top corners below the antenna band, two
# just above the slot line, two inside the slot; parts keep HOLE_KEEP from each centre
HOLES = [(77.5, 76.5, 2.2), (122.5, 76.5, 2.2), (77.5, 116.0, 2.2), (122.5, 116.0, 2.2),
         (81.0, 127.5, 2.2), (119.0, 127.5, 2.2)]   # the last two clear of the switch notch
HOLE_KEEP = 3.0
# parts allowed past the body edge (their mouths at the board edge)
AT_EDGE = ('J_USB', 'J_SD')
# the cell, on the shell's shelf over the component side: x0, y0, x1, y1 (30 x 50, clear of the
# antenna band and the two buttons), the shelf's top face above the board (the tallest parts under
# it, the module and the USB-C, are 3.1-3.2 mm: 0.4 mm clearance and a 0.8 mm shelf), its thickness
CELL = (88.0, 79.0, 118.0, 129.0)
SHELF_Z = 4.4
CELL_T = 5.0                    # thickest cell the shelf is drawn for (503050)

# ref -> (x, y, rotation deg CCW)  -- top view, y down
PLACE = {}


def place(key, x, y, rot=0):
    """placement.py names parts by design.py key; PLACE is by reference."""
    PLACE[K[key]] = (round(x, 4), round(y, 4), rot % 360)


def uid(*k):
    return gen_sch.uid('pcb', *k)


# ---------------------------------------------------------------------------
def rot_pt(x, y, a):
    r = math.radians(a)
    # KiCad: positive angle = CCW on screen (y down) -> x' = x cos + y sin, y' = -x sin + y cos
    return x * math.cos(r) + y * math.sin(r), -x * math.sin(r) + y * math.cos(r)


def load_fp(name):
    return parse(open(os.path.join(PRJ, D.LIB + '.pretty', name + '.kicad_mod')).read())


def canon(n):
    return n if n.startswith('unconnected') else n.rsplit('/', 1)[-1]


NETLIST = {}    # (ref, pad) -> the schematic's net name
FULL = {}       # design.py net name -> the schematic's (board's) net name


def schematic_netlist():
    """(ref, pad) -> net name, from the generated schematic (kicad-cli), so the
    board carries exactly the schematic's nets -- including KiCad's own
    unconnected-(...) names for no-connect pins."""
    fn = tmp('gen.net')
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', fn,
                    os.path.join(PRJ, D.PROJECT + '.kicad_sch')], check=True, capture_output=True)
    t = parse(open(fn).read())
    out, full = {}, {}
    for n in findall(find(t, 'nets'), 'net'):
        name = str(find(n, 'name')[1])
        full[canon(name)] = name
        for nd in findall(n, 'node'):
            out[(str(find(nd, 'ref')[1]), str(find(nd, 'pin')[1]))] = name
    return out, full


def NET(n):
    """design.py's net name -> the board's."""
    if not FULL:
        nl, full = schematic_netlist()
        NETLIST.update(nl)
        FULL.update(full)
    return FULL[n]


SMALL = re.compile(r'_0603_|_0805_|SOD-523|SOT-23|SOT-363|R_Array|AOTA|Crystal_SMD|WS2812|TSOT|TestPoint')


def instance(part, x, y, rot, path, sheetname, sheetfile, datasheet=''):
    fp = load_fp(part.footprint.split(':')[1])
    for i, e in enumerate(fp):   # legacy (fp_text reference/value ...) -> (property ...)
        if isinstance(e, list) and e and e[0] == 'fp_text' and e[1] in ('reference', 'value'):
            fp[i] = ['property', Q('Reference' if e[1] == 'reference' else 'Value'), e[2]] + e[3:]
    out = ['footprint', Q(part.footprint), ['layer', Q('F.Cu')], ['uuid', uid(part.ref)],
           ['at', x, y, rot] if rot else ['at', x, y]]
    for k in ('descr', 'tags'):
        e = find(fp, k)
        if e:
            out.append(e)
    fields = {'Reference': part.ref, 'Value': part.value, 'Footprint': part.footprint,
              'Datasheet': datasheet, 'Description': part.desc, 'MPN': part.mpn, 'LCSC': part.lcsc}
    done = set()
    for pr in findall(fp, 'property'):
        k = pr[1]
        if k in fields:
            pr = copy.deepcopy(pr)
            pr[2] = Q(fields[k])
            at = find(pr, 'at')
            ang = (float(at[3]) if len(at) > 3 else 0) + rot
            at[:] = ['at', float(at[1]), float(at[2]), ang % 360]
            pr = [e for e in pr if not (isinstance(e, list) and e and e[0] == 'uuid')]
            pr.insert(3, ['uuid', uid(part.ref, 'prop', k)])
            if k == 'Reference' and SMALL.search(part.footprint):
                pr = [e for e in pr if not (isinstance(e, list) and e and e[0] == 'effects')]
                pr.append(['effects', ['font', ['size', 0.8, 0.8], ['thickness', 0.12]]])
            out.append(pr); done.add(k)
    for k, v in fields.items():
        if k not in done:
            out.append(['property', Q(k), Q(v), ['at', 0, 0, rot], ['layer', Q('F.Fab')], ['hide', 'yes'],
                        ['uuid', uid(part.ref, 'prop', k)],
                        ['effects', ['font', ['size', 1.27, 1.27], ['thickness', 0.15]]]])
    out += [['path', Q(path)], ['sheetname', Q(sheetname)], ['sheetfile', Q(sheetfile)]]
    attr = find(fp, 'attr')
    a = list(attr) if attr else ['attr', 'smd']
    if not part.bom and 'exclude_from_bom' not in a:
        a.append('exclude_from_bom')
    if getattr(part, 'dnp', False) and 'dnp' not in a:
        a.append('dnp')
    out.append(a)
    for e in fp[2:]:
        if not isinstance(e, list) or not e:
            continue
        if e[0] in ('version', 'generator', 'generator_version', 'layer', 'descr', 'tags', 'property',
                    'attr', 'uuid', 'embedded_fonts'):
            continue
        if e[0] == 'fp_text':
            e = copy.deepcopy(e)
            at = find(e, 'at')
            ang = (float(at[3]) if len(at) > 3 else 0) + rot
            at[:] = ['at', float(at[1]), float(at[2]), ang % 360]
            if e[2] == '%R':
                e[2] = Q('${REFERENCE}')
            out.append(e)
        elif e[0] == 'pad':
            e = copy.deepcopy(e)
            at = find(e, 'at')
            ang = (float(at[3]) if len(at) > 3 else 0) + rot
            at[:] = ['at', float(at[1]), float(at[2])] + ([ang % 360] if ang % 360 else [])
            e = [x_ for x_ in e if not (isinstance(x_, list) and x_ and x_[0] in ('net', 'uuid'))]
            num = str(e[1])
            net = part.pins.get(num)
            if num and num not in part.pins and e[2] != 'np_thru_hole' and num not in part.nc_pads:
                raise SystemExit('%s pad %s has no pin in design.py' % (part.ref, num))
            if num and part.pins:
                sn = NETLIST.get((part.ref, num))
                if net and (sn is None or canon(sn) != net):
                    raise SystemExit('%s pad %s: design %s vs schematic %s' % (part.ref, num, net, sn))
                net = sn
            if net:
                e.append(['net', Q(net)])
            e.append(['uuid', uid(part.ref, 'pad', num, len(out))])
            out.append(e)
        elif e[0] == 'zone':  # footprint zones are stored in board coordinates
            e = copy.deepcopy(e)
            for pts in findall(find(e, 'polygon'), 'pts'):
                for xy in pts[1:]:
                    dx, dy = rot_pt(float(xy[1]), float(xy[2]), rot)
                    xy[1], xy[2] = round(x + dx, 4), round(y + dy, 4)
            # the S3 antenna keep-out lists In1..In30: keep the layers this stack has
            lay = find(e, 'layers')
            if lay:
                lay[1:] = [l for l in lay[1:] if str(l) in COPPER]
            out.append(e)
        else:
            out.append(copy.deepcopy(e))
    out.append(['embedded_fonts', 'no'])
    return out


COPPER = ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')


def board_only(name, fpname, x, y, desc):
    """A board-only footprint (fiducial, mounting hole): not in the schematic, BOM or CPL."""
    fp = load_fp(fpname)
    for i, e in enumerate(fp):
        if isinstance(e, list) and e and e[0] == 'fp_text' and e[1] in ('reference', 'value'):
            fp[i] = ['property', Q('Reference' if e[1] == 'reference' else 'Value'), e[2]] + e[3:]
    inst = ['footprint', Q(D.LIB + ':' + fpname), ['layer', Q('F.Cu')], ['uuid', uid(name)], ['at', x, y]]
    for e in fp[2:]:
        if not isinstance(e, list) or not e or e[0] in ('version', 'generator', 'generator_version', 'layer',
                                                        'embedded_fonts'):
            continue
        e = copy.deepcopy(e)
        if e[0] == 'property':
            if e[1] == 'Reference':
                e[2] = Q(name)
            if e[1] == 'Description':
                e[2] = Q(desc)
            e = [x_ for x_ in e if not (isinstance(x_, list) and x_ and x_[0] == 'uuid')]
            e.insert(3, ['uuid', uid(name, 'prop', e[1])])
        elif e[0] == 'pad':
            e = [x_ for x_ in e if not (isinstance(x_, list) and x_ and x_[0] == 'uuid')]
            e.append(['uuid', uid(name, 'pad', e[1])])
        elif e[0] == 'attr':        # not in the schematic: board only, no BOM, no position file
            e = ['attr'] + [a_ for a_ in e[1:] if a_ not in ('board_only', 'exclude_from_pos_files', 'exclude_from_bom')]
            e += ['board_only', 'exclude_from_pos_files', 'exclude_from_bom']
        inst.append(e)
    inst.append(['embedded_fonts', 'no'])
    return inst


def board_pads(board):
    """fanout.Pad list (absolute coordinates) + courtyard boxes by ref."""
    import fanout
    pads, crt = [], {}
    for fp in board:
        if not (isinstance(fp, list) and fp and fp[0] == 'footprint'):
            continue
        at = find(fp, 'at')
        fx, fy = float(at[1]), float(at[2])
        rot = float(at[3]) if len(at) > 3 else 0.0
        ref = [str(e[2]) for e in findall(fp, 'property') if e[1] == 'Reference'][0]
        xs, ys = [], []
        for g in fp:
            if isinstance(g, list) and g and g[0] in ('fp_rect', 'fp_line') and find(g, 'layer')[1] == 'F.CrtYd':
                for k in ('start', 'end'):
                    q = find(g, k)
                    dx, dy = rot_pt(float(q[1]), float(q[2]), rot)
                    xs.append(fx + dx); ys.append(fy + dy)
            elif isinstance(g, list) and g and g[0] == 'fp_circle' and find(g, 'layer')[1] == 'F.CrtYd':
                c, e_ = find(g, 'center'), find(g, 'end')
                cx_, cy_ = rot_pt(float(c[1]), float(c[2]), rot)
                rr = math.hypot(float(e_[1]) - float(c[1]), float(e_[2]) - float(c[2]))
                xs += [fx + cx_ - rr, fx + cx_ + rr]; ys += [fy + cy_ - rr, fy + cy_ + rr]
        if xs:
            crt[ref] = (min(xs), min(ys), max(xs), max(ys))
        for e in findall(fp, 'pad'):
            pat = find(e, 'at'); sz = find(e, 'size')
            dx, dy = rot_pt(float(pat[1]), float(pat[2]), rot)
            pang = (float(pat[3]) if len(pat) > 3 else 0.0) % 180
            w, h = float(sz[1]), float(sz[2])
            if abs(pang - 90) < 1:
                w, h = h, w
            elif pang not in (0.0,):
                w = h = max(w, h)
            net = find(e, 'net')
            layers = [str(x_) for x_ in find(e, 'layers')[1:]]
            th = e[2] in ('thru_hole', 'np_thru_hole')
            if th:
                layers = ['F.Cu', 'B.Cu']
            pads.append(fanout.Pad(ref, str(e[1]), str(net[1]) if net else None, fx + dx, fy + dy,
                                   w / 2, h / 2, layers, th, (fx, fy)))
    return pads, crt


# ---------------------------------------------------------------------------
def seg(x0, y0, x1, y1, w, layer, net, key, locked=True):
    s = ['segment', ['start', round(x0, 4), round(y0, 4)], ['end', round(x1, 4), round(y1, 4)],
         ['width', w], ['layer', Q(layer)]]
    if locked:
        s.append(['locked', 'yes'])
    return s + [['net', Q(net)], ['uuid', uid(*key)]]


def via(x, y, net, key, size=0.6, drill=0.3):
    return ['via', ['at', round(x, 4), round(y, 4)], ['size', size], ['drill', drill],
            ['layers', Q('F.Cu'), Q('B.Cu')], ['locked', 'yes'], ['net', Q(net)], ['uuid', uid(*key)]]


def footprint_of(board, ref):
    return [e for e in board if isinstance(e, list) and e and e[0] == 'footprint'
            and any(p[1] == 'Reference' and p[2] == ref for p in findall(e, 'property'))][0]



def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        (xa, ya), (xb, yb) = poly[i], poly[(i + 1) % n]
        if (ya > y) != (yb > y) and x < xa + (y - ya) * (xb - xa) / (yb - ya):
            inside = not inside
    return inside


def outline():
    """Edge.Cuts: OUTLINE's segments, the two insertion-edge corners as 0.9 mm arcs (a GB
    cartridge's), the rest straight."""
    g = []
    n = len(OUTLINE)
    r, k = CH_TAB, CH_TAB * (1 - 2 ** -0.5)
    arcs = {((TAB_X1, Y1 - r), (TAB_X1 - r, Y1)): (TAB_X1 - k, Y1 - k),
            ((TAB_X0 + r, Y1), (TAB_X0, Y1 - r)): (TAB_X0 + k, Y1 - k)}
    for i in range(n):
        a, b = OUTLINE[i], OUTLINE[(i + 1) % n]
        st = ['stroke', ['width', 0.1], ['type', 'default']]
        if (a, b) in arcs:
            m = arcs[(a, b)]
            g.append(['gr_arc', ['start', *a], ['mid', round(m[0], 4), round(m[1], 4)], ['end', *b], st,
                      ['layer', Q('Edge.Cuts')], ['uuid', uid('edge', i)]])
        else:
            g.append(['gr_line', ['start', *a], ['end', *b], st, ['layer', Q('Edge.Cuts')], ['uuid', uid('edge', i)]])
    return g


def zone(name, net, layer, pts, keepout=False, priority=0, no_parts=False):
    z = ['zone', ['net', Q(net)] if net else ['net', Q('')], ['layer', Q(layer)], ['uuid', uid('zone', name, layer)],
         ['name', Q(name)], ['hatch', 'edge', 0.5]]
    if priority:
        z.append(['priority', priority])
    z += [['connect_pads', ['clearance', 0 if keepout else 0.25]], ['min_thickness', 0.25]]
    if keepout:
        z.append(['keepout', ['tracks', 'allowed' if no_parts else 'not_allowed'], ['vias', 'allowed' if no_parts else 'not_allowed'],
                  ['pads', 'allowed'], ['copperpour', 'allowed' if no_parts else 'not_allowed'],
                  ['footprints', 'not_allowed' if no_parts else 'allowed']])
        z.append(['placement', ['enabled', 'no'], ['sheetname', Q('')]])
    z.append(['fill', 'yes', ['thermal_gap', 0.3], ['thermal_bridge_width', 0.4], ['island_removal_mode', 0]]
             if not keepout else
             ['fill', ['thermal_gap', 0.5], ['thermal_bridge_width', 0.5], ['island_removal_mode', 0]])
    z.append(['polygon', ['pts'] + [['xy', round(x, 4), round(y, 4)] for x, y in pts]])
    return z


def circle_pts(x, y, r, n=12):
    return [(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def text(s, x, y, layer, size=1.0, mirror=False, rot=0):
    eff = ['effects', ['font', ['size', size, size], ['thickness', size * 0.15]]]
    if mirror:
        eff.append(['justify', 'mirror'])
    return ['gr_text', Q(s), ['at', x, y, rot], ['layer', Q(layer)], ['uuid', uid('text', s, layer)], eff]




# ---------------------------------------------------------------------------
from placement import do_placement  # noqa: E402

NETCLASSES = [  # name, clearance, track, via dia, via drill, design.py nets
    ('PWR', 0.15, 0.5, 0.8, 0.4, ['VBAT']),
    # the TPS63001's nets reach 0.24 mm pins at 0.5 mm pitch: 0.3 mm tracks (about 1 A, short runs)
    ('REG', 0.15, 0.3, 0.6, 0.3, ['VSYS', 'REG_L1', 'REG_L2', '+3V3']),
    ('VBUS', 0.15, 0.4, 0.6, 0.3, ['VBUS', 'CART_VCC']),
    ('USB', 0.15, 0.25, 0.6, 0.3, ['UBRG_DP', 'UBRG_DM']),
]


def configure_project():
    """Design rules + net classes in the .kicad_pro (JLCPCB 4-layer capable: the USB-C D- crossover
    uses 0.45 / 0.2 mm vias, inside JLCPCB's 4-layer minimum)."""
    fn = os.path.join(PRJ, D.PROJECT + '.kicad_pro')
    pro = json.load(open(fn))
    r = pro['board']['design_settings']['rules']
    r.update({'min_clearance': 0.15, 'min_copper_edge_clearance': 0.3, 'min_track_width': 0.15,
              'min_via_diameter': 0.45, 'min_through_hole_diameter': 0.2, 'min_hole_clearance': 0.25,
              'min_hole_to_hole': 0.25, 'min_via_annular_width': 0.125, 'solder_mask_min_width': 0.0,
              'solder_mask_clearance': 0.0, 'solder_mask_to_copper_clearance': 0.0})
    pro['board']['design_settings'].setdefault('rule_severities', {})['solder_mask_bridge'] = 'warning'
    ns = pro['net_settings']
    base = dict(ns['classes'][0])
    base.update({'name': 'Default', 'clearance': 0.15, 'track_width': 0.2, 'via_diameter': 0.6, 'via_drill': 0.3})
    classes = [base]
    patterns = []
    for i, (name, cl, tw, vd, vdr, nets) in enumerate(NETCLASSES):
        c = dict(base)
        c.update({'name': name, 'clearance': cl, 'track_width': tw, 'via_diameter': vd, 'via_drill': vdr,
                  'priority': i})
        classes.append(c)
        patterns += [{'netclass': name, 'pattern': NET(n)} for n in nets]
    ns['classes'] = classes
    ns['netclass_patterns'] = patterns
    ns['netclass_assignments'] = None
    pro['pcbnew'] = pro.get('pcbnew', {})
    pro['pcbnew'].setdefault('last_paths', {})['specctra_dsn'] = ''
    json.dump(pro, open(fn, 'w'), indent=2)
    open(fn, 'a').write('\n')
    solid = ' || '.join("A.memberOfFootprint('%s')" % K[k] for k in ('U_UART', 'U_REG', 'J_USB'))
    open(os.path.join(PRJ, D.PROJECT + '.kicad_dru'), 'w').write(
        '(version 1)\n'
        # QFN / VSON exposed pads and the USB-C shell legs join the planes and pours solidly
        '(rule "gnd_solid_under_ics"\n'
        '\t(condition "A.NetName == \'GND\' && (%s)")\n'
        '\t(constraint zone_connection solid))\n'
        # the fingers: pins 1 and 32 are 0.55 mm from the tab's sides, every finger 1.0-1.5 mm from
        # the insertion edge, as on a GB cartridge
        '(rule "finger_edge"\n'
        '\t(condition "A.memberOfFootprint(\'%s\')")\n'
        '\t(constraint edge_clearance (min 0.5mm)))\n'
        # the USB-C and microSD mouths sit at the board edge by design
        '(rule "connectors_at_edge"\n'
        '\t(condition "A.memberOfFootprint(\'%s\') || A.memberOfFootprint(\'%s\')")\n'
        '\t(constraint edge_clearance (min 0mm)))\n'
        % (solid, K['J_EDGE'], K['J_USB'], K['J_SD']))


def regulator_preroute():
    """The TPS63001's pins (VSON-10, 0.24 mm pads at 0.5 mm pitch), routed here as the datasheet
    lays them out, so no router meets them at an angle: L1 / L2 straight west into the inductor's
    pads; VIN (pin 5) down into C_REGIN, VOUT (pin 1) up into C_REGOUT1; VINA (pin 8) east into
    C_VINA; EN (pin 6) east and down, for the router to take on.  0.3 mm, 0.2 for EN.
    Returns [(x0, y0, x1, y1, design net, width)]."""
    cx, cy, _ = PLACE[K['U_REG']]
    ix = 1.4                                       # pad centres at +-1.4
    cregin = PLACE[K['C_REGIN']][1]
    cout = PLACE[K['C_REGOUT1']][1]
    cvina = PLACE[K['C_VINA']][0]
    w = 0.3
    return [
        (cx - ix, cy + 0.5, cx - 2.1, cy + 0.5, 'REG_L1', w), (cx - 2.1, cy + 0.5, cx - 2.7, cy + 1.1, 'REG_L1', w),
        (cx - ix, cy - 0.5, cx - 2.1, cy - 0.5, 'REG_L2', w), (cx - 2.1, cy - 0.5, cx - 2.7, cy - 1.1, 'REG_L2', w),
        (cx - ix, cy + 1.0, cx - ix, cregin, 'VSYS', w),
        (cx - ix, cy - 1.0, cx - ix, cout, '+3V3', w),
        (cx + ix, cy, cvina, cy, 'VSYS', w),
        (cx + ix, cy + 1.0, cx + 2.1, cy + 1.0, 'PWR_EN', 0.2), (cx + 2.1, cy + 1.0, cx + 2.1, cy + 2.6, 'PWR_EN', 0.2),
        # VIN and VINA joined round the IC's south side, through their capacitors' pads
        (cx - ix, cregin, cx - ix, cregin + 1.2, 'VSYS', w), (cx - ix, cregin + 1.2, cvina + 1.0, cregin + 1.2, 'VSYS', w),
        (cvina + 1.0, cregin + 1.2, cvina + 1.0, cy, 'VSYS', w), (cvina, cy, cvina + 1.0, cy, 'VSYS', w),
    ]


def regulator_vias():
    """EN leaves the pre-route on B.Cu (the VSYS loop closes the IC's south side on F.Cu)."""
    cx, cy, _ = PLACE[K['U_REG']]
    return [(cx + 2.1, cy + 2.6, 'PWR_EN')]


def add_fanout(board):
    """The regulator's pre-route; plane vias for every F.Cu pad on GND / +3V3 (fanout.py) not
    already served by it, the QFN / VSON exposed-pad arrays; the cell's ground lead pad (B.Cu) gets
    its own stub and via."""
    import fanout
    pads, crt = board_pads(board)
    pre = [(round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4), NET(n), w) for x0, y0, x1, y1, n, w in regulator_preroute()]
    for i, (x0, y0, x1, y1, n, w) in enumerate(pre):
        board.append(seg(x0, y0, x1, y1, w, 'F.Cu', n, ('reg', i)))
    pre_v = [(round(x, 4), round(y, 4), NET(n)) for x, y, n in regulator_vias()]
    for i, (x, y, n) in enumerate(pre_v):
        board.append(via(x, y, n, ('regv', i)))
    served = {id(p) for p in pads for (x0, y0, x1, y1, n, w) in pre
              if p.net == n and (p.dist(x0, y0) < 1e-6 or p.dist(x1, y1) < 1e-6)}
    # the hand routes (USB-C pair, UART0 escapes, the GND finger) go down before the fan-out and are
    # handed to it as existing copper, so its plane vias and stubs keep clear of them
    early = []
    # USB-C D+ / D-: the two rows interleave (B7 DM, A6 DP, A7 DM, B6 DP at local x -0.75 .. +0.75,
    # pads ending at local y -4.77, inward = -y).  DP joins on F.Cu in a loop inward of the pads;
    # DM drops through two 0.45 / 0.2 mm vias and joins on B.Cu across under the loop.
    ux, uy, ur = PLACE[K['J_USB']]
    def U(lx, ly):
        dx, dy = rot_pt(lx, ly, ur)
        return round(ux + dx, 4), round(uy + dy, 4)
    dp, dm, ye, w = NET('UBRG_DP'), NET('UBRG_DM'), -4.77, 0.2
    pts = [U(-0.25, ye + 0.3), U(-0.25, -5.7), U(0.75, -5.7), U(0.75, ye + 0.3)]
    for i, (p0, p1) in enumerate(zip(pts, pts[1:])):
        early.append(seg(*p0, *p1, w, 'F.Cu', dp, ('usb', 'dp', i)))
    for k, lx in enumerate((-0.75, 0.25)):
        early.append(seg(*U(lx, ye + 0.3), *U(lx, -5.1), w, 'F.Cu', dm, ('usb', 'dm', k)))
        early.append(via(*U(lx, -5.1), dm, ('usb', 'dmv', k), 0.45, 0.2))
    early.append(seg(*U(-0.75, -5.1), *U(0.25, -5.1), w, 'B.Cu', dm, ('usb', 'dmb')))
    # on to the ESD diodes, so the routers start past the crossover: DP from the loop's north
    # corner on F.Cu to D_ESDP's pad; DM on B.Cu past the loop, up through a via by D_ESDM's pad
    ep = [p for p in pads if p.ref == K['D_ESDP'] and p.net == dp][0]
    em = [p for p in pads if p.ref == K['D_ESDM'] and p.net == dm][0]
    a0 = U(-0.25, -5.7)
    early.append(seg(*a0, ep.cx - 1.15, ep.cy, w, 'F.Cu', dp, ('usb', 'dpe', 0)))
    early.append(seg(ep.cx - 1.15, ep.cy, ep.cx, ep.cy, w, 'F.Cu', dp, ('usb', 'dpe', 1)))
    m0, mv = U(0.25, -5.1), (round(em.cx - 1.0, 4), round(em.cy, 4))
    early.append(seg(*m0, mv[0] - (em.cy - m0[1]), em.cy, w, 'B.Cu', dm, ('usb', 'dme', 0)))
    early.append(seg(mv[0] - (em.cy - m0[1]), em.cy, *mv, w, 'B.Cu', dm, ('usb', 'dme', 1)))
    early.append(via(*mv, dm, ('usb', 'dmev'), 0.45, 0.2))
    early.append(seg(*mv, em.cx, em.cy, w, 'F.Cu', dm, ('usb', 'dme', 2)))
    # ... and from the diodes to the CP2102N on B.Cu, under the SS34 and the power path, up through
    # vias in front of its pins 4 (DP) and 5 (DM), staggered so the two vias clear each other
    u4 = [p for p in pads if p.ref == K['U_UART'] and p.num == '4'][0]
    u5 = [p for p in pads if p.ref == K['U_UART'] and p.num == '5'][0]
    for net, e, u, dy, k in ((dp, ep, u4, -0.3, 'p'), (dm, em, u5, 0.3, 'm')):
        w0 = (round(e.cx + 1.2, 4), e.cy)                      # via east of the diode's pad
        w1 = (round(u.cx - u.hw - 0.95, 4), round(u.cy + dy, 4))   # via west of the chip's pin
        early.append(seg(e.cx, e.cy, *w0, w, 'F.Cu', net, ('usbb', k, 'a')))
        early.append(via(*w0, net, ('usbb', k, 'v0'), 0.45, 0.2))
        jog = w1[1] - w0[1]
        mid = (round(w0[0] + abs(jog), 4), w1[1])
        early.append(seg(*w0, *mid, w, 'B.Cu', net, ('usbb', k, 'b0')))
        early.append(seg(*mid, *w1, w, 'B.Cu', net, ('usbb', k, 'b1')))
        early.append(via(*w1, net, ('usbb', k, 'v1'), 0.45, 0.2))
        knee = (round(u.cx - u.hw - 0.4, 4), u.cy)
        early.append(seg(*w1, *knee, w, 'F.Cu', net, ('usbb', k, 'c0')))
        early.append(seg(*knee, u.cx, u.cy, w, 'F.Cu', net, ('usbb', k, 'c1')))
    # UART0 (module pads 37 TXD0 / 36 RXD0, on its east side): the gap to the microSD takes one
    # track, not two, so both drop to B.Cu right at the module and run down to the CP2102N there
    mx, my, _ = PLACE[K['U_S3']]
    for k, (pad_dy, net, vdy) in enumerate(((-1.45, 'S3_TXD', -0.7), (-0.18, 'S3_RXD', 0.7))):
        px, py = mx + 8.75, my + pad_dy
        x1, vx, vy = px + 0.75, px + 1.45, py + vdy
        early.append(seg(px, py, x1, py, 0.2, 'F.Cu', NET(net), ('uart0', k, 'a')))
        early.append(seg(x1, py, vx, vy, 0.2, 'F.Cu', NET(net), ('uart0', k, 'b')))
        early.append(via(vx, vy, NET(net), ('uart0', k, 'v')))
    # the GND finger (pin 32): a locked stub up out of the tab and two vias into In1
    j = [p for p in pads if p.ref == K['J_EDGE'] and p.num == '32'][0]
    top = j.cy - j.hh
    yv = TAB_Y - 1.2
    early.append(seg(j.cx, top + 0.3, j.cx, yv, 0.8, 'F.Cu', 'GND', ('f32', 's')))
    for k, dx in enumerate((-0.55, 0.55)):
        early.append(via(j.cx + dx, yv, 'GND', ('f32', 'v', k), 0.8, 0.4))
    early.append(seg(j.cx - 0.55, yv, j.cx + 0.55, yv, 0.8, 'F.Cu', 'GND', ('f32', 'h')))
    board += early
    for e in early:
        n = str(find(e, 'net')[1])
        if e[0] == 'segment':
            s0, s1 = find(e, 'start'), find(e, 'end')
            pre.append((float(s0[1]), float(s0[2]), float(s1[1]), float(s1[2]), n, float(find(e, 'width')[1])))
        else:
            at = find(e, 'at')
            pre_v.append((float(at[1]), float(at[2]), n))
    served |= {id(p) for p in pads for (x0, y0, x1, y1, n, w) in pre
               if p.net == n and (p.dist(x0, y0) < 1e-6 or p.dist(x1, y1) < 1e-6)}
    keep = [crt[K[k]] for k in ('U_S3', 'J_USB', 'SW_S3EN', 'SW_S3BOOT') if K[k] in crt]
    sx, sy, _ = PLACE[K['U_S3']]                       # the antenna keep-out band
    keep.append((X0, Y0 - 1.0, X1, sy - 6.75 + 0.3))
    holes = [(x, y, d / 2 + 0.5) for x, y, d in HOLES]
    vias, segs, failed = fanout.plan(pads, keep, (X0, Y0, X1, TAB_Y), TAB_Y, holes,
                                     skip_refs=(K['J_EDGE'],), extra_segs=pre, extra_vias=pre_v,
                                     skip_pads=served)
    for i, (x, y, n) in enumerate(vias):
        board.append(via(x, y, n, ('fv', i), fanout.VIA_D, fanout.VIA_DRILL))
    for i, (x0, y0, x1, y1, n, w) in enumerate(segs):
        board.append(seg(x0, y0, x1, y1, round(w, 3), 'F.Cu', n, ('fs', i)))
    print('fan-out: %d vias, %d stubs%s' % (len(vias), len(segs), ('; FAILED: ' + ' '.join(failed)) if failed else ''))


def check_parts_inside(board):
    """Every courtyard inside the body (the tab is the edge's alone; USB-C and microSD may reach the
    side edges), clear of the shell holes, no two overlapping."""
    _, crt = board_pads(board)
    bad = []
    for p in D.PARTS:
        if p.ref == K['J_EDGE'] or p.ref not in crt:
            continue
        x0, y0, x1, y1 = crt[p.ref]
        edge_ok = p.key in AT_EDGE
        if (not edge_ok and (x0 < X0 + 0.3 or x1 > X1 - 0.3)) or y0 < Y0 + 0.1 or y1 > TAB_Y - 0.3:
            bad.append('%s (%s) courtyard %.1f,%.1f..%.1f,%.1f outside the body' % (p.ref, p.key, x0, y0, x1, y1))
        if x0 < NOTCH[2] + 0.3 and y1 > NOTCH[1] - 0.3:
            bad.append('%s (%s) courtyard reaches the switch notch' % (p.ref, p.key))
        for hx, hy, hd in HOLES:
            cx, cy = min(max(hx, x0), x1), min(max(hy, y0), y1)
            if math.hypot(cx - hx, cy - hy) < HOLE_KEEP:
                bad.append('%s (%s) within %.1f mm of the hole at %g,%g' % (p.ref, p.key, HOLE_KEEP, hx, hy))
    refs = sorted(r for r in crt if (r in D.BY_REF and r != K['J_EDGE']) or r.startswith('FID'))
    for i, r1 in enumerate(refs):
        a = crt[r1]
        for r2 in refs[i + 1:]:
            b = crt[r2]
            if a[0] < b[2] - 0.01 and b[0] < a[2] - 0.01 and a[1] < b[3] - 0.01 and b[1] < a[3] - 0.01:
                kk = lambda r: D.BY_REF[r].key if r in D.BY_REF else r
                bad.append('%s (%s) and %s (%s): courtyards overlap' % (r1, kk(r1), r2, kk(r2)))
    if bad:
        raise SystemExit('placement:\n  ' + '\n  '.join(bad))


def write_case_anchors():
    """case/board-anchors.scad and .json: what the shell needs from the board."""
    def at(key):
        x, y, _ = PLACE[K[key]]
        return [x, y]
    a = {
        'frame': 'KiCad board frame, mm, y down; F.Cu (every part) is the front, B.Cu (the cell) the back',
        'outline': [list(p) for p in OUTLINE], 'thickness': THICKNESS,
        'body': [X0, Y0, X1, TAB_Y], 'tab': [TAB_X0, TAB_Y, TAB_X1, Y1], 'insertion_edge_y': Y1,
        'slot_y_estimate': SLOT_Y, 'lip_y_estimate': LIP_Y,
        'holes': [list(h) for h in HOLES],
        'switch_notch': list(NOTCH),
        'cell_on_shelf': list(CELL), 'shelf_top_z': SHELF_Z, 'cell_max_thickness': CELL_T,
        'cell_leads': [PLACE[K['J_BAT']][0], PLACE[K['J_BAT']][1]],
        'usb_c_west': [X0, PLACE[K['J_USB']][1]], 'microsd_east': [X1, PLACE[K['J_SD']][1]],
        'sw_s3_en': at('SW_S3EN'), 'sw_s3_boot': at('SW_S3BOOT'),
        'led_wifi': at('D_LWIFI'), 'led_bus': at('D_LBUS'), 'led_charge': at('D_CHG'),
        'antenna': [PLACE[K['U_S3']][0], Y0, 'keep the shell wall thin and metal-free over the top 7 mm'],
        'front_max_height': 3.3, 'note': 'front: ESP32-S3 module 3.1 mm, USB-C 3.2 mm, microSD 1.8 mm',
    }
    os.makedirs(os.path.join(PRJ, 'case'), exist_ok=True)
    json.dump(a, open(os.path.join(PRJ, 'case', 'board-anchors.json'), 'w'), indent=1)
    v = lambda p: '[%s]' % ', '.join('%g' % c for c in p)
    lines = ['// GENERATED by tools/gen_pcb.py from tools/placement.py -- do not edit.',
             '// KiCad board frame (mm, y down).  F.Cu (every part) is the front; the back lies against the Pocket.',
             'pcb_outline = [%s];' % ', '.join(v(p) for p in OUTLINE),
             'pcb_t = %g;' % THICKNESS,
             'pcb_body = %s;   // x0, y0 (top edge), x1, y1 (tab base)' % v((X0, Y0, X1, TAB_Y)),
             'pcb_tab = %s;    // x0, y0, x1, y1 (insertion edge)' % v((TAB_X0, TAB_Y, TAB_X1, Y1)),
             'slot_y = %g;      // the Pocket\'s shell top, ESTIMATE: inside the slot below this' % SLOT_Y,
             'pcb_holes = [%s];   // [x, y, diameter]: M2' % ', '.join(v(h) for h in HOLES),
             'switch_notch = %s;   // x0, y0, x1, y1 cut from the board by the voltage switch (ESTIMATE)' % v(NOTCH),
             'lip_y = %g;       // the Pocket\'s lip, ESTIMATE: it covers the component side below this' % LIP_Y,
             'cell = %s;   // x0, y0, x1, y1 of the cell on the shelf over the component side' % v(CELL),
             'shelf_z = %g;     // the shelf\'s top face above the board; the cell sits on it' % SHELF_Z,
             'cell_leads = %s;  // the lead pads (+ at x + 3, - at x - 3)' % v(PLACE[K['J_BAT']][:2]),
             'cell_t = %g;' % CELL_T,
             'usb_c = %s;       // mouth on the west edge' % v(a['usb_c_west']),
             'microsd = %s;     // mouth on the east edge' % v(a['microsd_east']),
             'sw_s3_en = %s;   // ESP32-S3 reset' % v(at('SW_S3EN')),
             'sw_s3_boot = %s; // ESP32-S3 BOOT' % v(at('SW_S3BOOT')),
             'led_wifi = %s;' % v(at('D_LWIFI')), 'led_bus = %s;' % v(at('D_LBUS')),
             'led_charge = %s;' % v(at('D_CHG')),
             'antenna_x = %g;   // the antenna: top edge, centre' % PLACE[K['U_S3']][0], '']
    open(os.path.join(PRJ, 'case', 'board-anchors.scad'), 'w').write('\n'.join(lines))


FIDUCIALS = []


def main():
    configure_project()
    do_placement(place, FIDUCIALS)
    write_case_anchors()
    NET('GND')
    hdr = parse(open(os.path.join(HERE, 'pcb_header.sexpr')).read())
    find(find(hdr, 'general'), 'thickness')[1] = THICKNESS
    setup = find(hdr, 'setup')
    setup.insert(2, ['solder_mask_min_width', 0])
    layers = find(hdr, 'layers')
    rest = [l for l in layers[1:] if not str(l[1]).endswith('.Cu')]
    kinds = {'F.Cu': 'signal', 'In1.Cu': 'power', 'In2.Cu': 'power', 'B.Cu': 'signal'}
    ids = {'F.Cu': '0', 'B.Cu': '2', 'In1.Cu': '4', 'In2.Cu': '6'}
    layers[1:] = [[ids[n], Q(n), kinds[n]] for n in COPPER] + rest
    board = hdr
    missing = [p.ref for p in D.PARTS if p.ref not in PLACE]
    if missing:
        raise SystemExit('unplaced: ' + ' '.join('%s (%s)' % (r, D.BY_REF[r].key) for r in missing))
    syms = gen_sch.load_symbols()
    for p in D.PARTS:
        x, y, r = PLACE[p.ref]
        u = gen_sch.units_of(syms[p.lib_id])[0]
        path = '/%s/%s' % (gen_sch.uid('sheet', p.sheet), gen_sch.uid(p.sheet, p.ref, u))
        path = path.replace('"', '')
        ds = p.ds
        for pr in findall(syms[p.lib_id], 'property'):
            if pr[1] == 'Datasheet' and not ds:
                ds = str(pr[2])
        board.append(instance(p, x, y, r, path, '/%s/' % p.sheet, p.sheet + '.kicad_sch', ds))
    for name, x, y in FIDUCIALS:
        board.append(board_only(name, 'Fiducial_1mm_Mask2mm', x, y, 'assembly fiducial'))
    for i, (x, y, d) in enumerate(HOLES):
        board.append(board_only('H%d' % (i + 1), 'MountingHole_2.2mm_M2', x, y, 'shell M2'))
    check_parts_inside(board)
    add_fanout(board)
    board += outline()
    # the tab: no vias, pour or inner copper (tracks reach the fingers)
    tab_all = [(TAB_X0 - 0.5, TAB_Y), (TAB_X1 + 0.5, TAB_Y), (TAB_X1 + 0.5, Y1 + 1), (TAB_X0 - 0.5, Y1 + 1)]
    for L in ('In1.Cu', 'In2.Cu'):
        board.append(zone('tab_no_copper_' + L[2], None, L, tab_all, keepout=True))
    for L in ('F.Cu', 'B.Cu'):
        z = zone('tab_no_pour_' + L[0], None, L, tab_all, keepout=True)
        find(z, 'keepout')[1:] = [['tracks', 'allowed'], ['vias', 'not_allowed'], ['pads', 'allowed'],
                                  ['copperpour', 'not_allowed'], ['footprints', 'allowed']]
        board.append(z)
    for i, (x, y, d) in enumerate(HOLES):   # the shell holes: no copper near them
        for L in COPPER:
            board.append(zone('hole_%d' % i, None, L, circle_pts(x, y, d / 2 + 0.6), keepout=True))
    # the cell's place on the shell's shelf, for the shell (F.Fab)
    c = CELL
    for i, (p0, p1) in enumerate((((c[0], c[1]), (c[2], c[1])), ((c[2], c[1]), (c[2], c[3])),
                                   ((c[2], c[3]), (c[0], c[3])), ((c[0], c[3]), (c[0], c[1])))):
        board.append(['gr_line', ['start', *p0], ['end', *p1], ['stroke', ['width', 0.15], ['type', 'dash']],
                      ['layer', Q('F.Fab')], ['uuid', uid('cellbox', i)]])
    board.append(text('LiPo <= 30 x 50 x 5 on the shell shelf, %g mm up' % SHELF_Z, (c[0] + c[2]) / 2, c[1] + 1.5, 'F.Fab', 0.8))
    board.append(zone('GND_plane', 'GND', 'In1.Cu', BODY))
    board.append(zone('3V3_plane', '+3V3', 'In2.Cu', BODY))
    # where the Pocket's shell top falls (estimate), on the drawing layers
    board.append(['gr_line', ['start', X0, SLOT_Y], ['end', X1, SLOT_Y], ['stroke', ['width', 0.15], ['type', 'dash']],
                  ['layer', Q('B.Fab')], ['uuid', uid('slotline')]])
    board.append(text('Pocket top (estimate): the back lies against the Pocket below', XC, SLOT_Y + 1.2, 'B.Fab', 0.8,
                      mirror=True))
    board.append(['gr_line', ['start', X0, LIP_Y], ['end', X1, LIP_Y], ['stroke', ['width', 0.15], ['type', 'dash']],
                  ['layer', Q('F.Fab')], ['uuid', uid('lipline')]])
    board.append(text('Pocket lip (estimate): low parts only below', XC, LIP_Y + 1.2, 'F.Fab', 0.8))
    board.append(text('FujiNet Pocket Rev0', 100.0, 134.4, 'F.SilkS', 1.0))
    board.append(text('github.com/FujiNetWIFI', XC, 137.4, 'B.SilkS', 1.0, mirror=True))
    board.append(text('CERN-OHL-W-2.0  FujiNet Pocket Rev0', XC, 139.4, 'B.SilkS', 0.8, mirror=True))
    board.append(['embedded_fonts', 'no'])
    open(PCB, 'w').write(dump(board) + '\n')
    print('placed %d parts -> %s' % (len(D.PARTS), os.path.basename(PCB)))


if __name__ == '__main__':
    main()
