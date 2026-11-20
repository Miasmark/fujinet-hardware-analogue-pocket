#!/usr/bin/env python3
"""Write 3d/LiPo_cell_30x50x4.step: a plain box standing in for the 1S LiPo cell, so the board's
STEP export (for the shell) and the renders show the cell where the shell's shelf holds it: over
the components on the component side, at gen_pcb.CELL (x, y) and gen_pcb.SHELF_Z above the board.
30 x 50 x 4 mm (a 403050; the shelf is drawn for up to 5 mm, gen_pcb.CELL_T).  The box is written
in the frame of the lead pads' footprint (J_BAT, placement.py), whose model it is: KiCad puts a
front footprint's model origin on the board's top face, its +y = the board's -y.

The STEP is written by hand (AP214, one manifold solid brep of six planar faces); no CAD library
is needed.

Usage: python3 tools/make_cell_step.py
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, '..', '3d', 'LiPo_cell_30x50x4.step')
H = 4.0


def cell_box():
    """(x0, x1, y0, y1, z0, z1) of the cell in J_BAT's model frame."""
    import gen_pcb as G
    G.do_placement(G.place, [])
    fx, fy, rot = G.PLACE[G.K['J_BAT']]
    assert rot == 0
    cx0, cy0, cx1, cy1 = G.CELL
    return (cx0 - fx, cx1 - fx, -(cy1 - fy), -(cy0 - fy), G.SHELF_Z, G.SHELF_Z + H)


def main():
    ents = []

    def e(s):
        ents.append(s)
        return '#%d' % (len(ents) + 99)       # entity ids start at 100

    x0, x1, y0, y1, z0, z1 = cell_box()
    P = {}
    for i, x in enumerate((x0, x1)):
        for j, y in enumerate((y0, y1)):
            for k, z in enumerate((z0, z1)):
                P[(i, j, k)] = (x, y, z)
    vtx = {key: e("VERTEX_POINT('',%s)" % e("CARTESIAN_POINT('',(%g,%g,%g))" % p)) for key, p in P.items()}
    edges = {}

    def edge(a, b):
        k = tuple(sorted((a, b)))
        if k not in edges:
            pa, pb = P[k[0]], P[k[1]]
            d = [pb[n] - pa[n] for n in range(3)]
            ln = max(abs(c) for c in d)
            dr = e("DIRECTION('',(%g,%g,%g))" % tuple(c / ln for c in d))
            line = e("LINE('',%s,%s)" % (e("CARTESIAN_POINT('',(%g,%g,%g))" % pa), e("VECTOR('',%s,%g)" % (dr, ln))))
            edges[k] = e("EDGE_CURVE('',%s,%s,%s,.T.)" % (vtx[k[0]], vtx[k[1]], line))
        return edges[k], (a, b) == tuple(sorted((a, b)))

    # faces: vertex loops counter-clockwise seen from outside, outward normal, a reference direction
    faces = [
        ([(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)], (0, 0, -1), (1, 0, 0)),   # z0
        ([(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], (0, 0, 1), (1, 0, 0)),    # z1
        ([(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], (0, -1, 0), (1, 0, 0)),   # y0
        ([(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)], (0, 1, 0), (1, 0, 0)),    # y1
        ([(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)], (-1, 0, 0), (0, 1, 0)),   # x0
        ([(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], (1, 0, 0), (0, 1, 0)),    # x1
    ]
    fids = []
    for loop, n, rd in faces:
        oes = []
        for a, b in zip(loop, loop[1:] + loop[:1]):
            ec, fwd = edge(a, b)
            oes.append(e("ORIENTED_EDGE('',*,*,%s,%s)" % (ec, '.T.' if fwd else '.F.')))
        el = e("EDGE_LOOP('',(%s))" % ','.join(oes))
        fb = e("FACE_OUTER_BOUND('',%s,.T.)" % el)
        ax = e("AXIS2_PLACEMENT_3D('',%s,%s,%s)" % (e("CARTESIAN_POINT('',(%g,%g,%g))" % P[loop[0]]),
                                                  e("DIRECTION('',(%g,%g,%g))" % n), e("DIRECTION('',(%g,%g,%g))" % rd)))
        fids.append(e("ADVANCED_FACE('',(%s),%s,.T.)" % (fb, e("PLANE('',%s)" % ax))))
    shell = e("CLOSED_SHELL('',(%s))" % ','.join(fids))
    brep = e("MANIFOLD_SOLID_BREP('LiPo cell',%s)" % shell)
    origin = e("AXIS2_PLACEMENT_3D('',%s,%s,%s)" % (e("CARTESIAN_POINT('',(0.,0.,0.))"), e("DIRECTION('',(0.,0.,1.))"),
                                                   e("DIRECTION('',(1.,0.,0.))")))
    body = '\n'.join('#%d = %s;' % (i + 100, s) for i, s in enumerate(ents))
    txt = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('LiPo cell stand-in, 30 x 50 x 4 mm'),'2;1');
FILE_NAME('LiPo_cell_30x50x4.step','2026-11-20T00:00:00',('FujiNet Pocket Rev0'),(''),'make_cell_step.py','','');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));
ENDSEC;
DATA;
#1 = APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#2);
#2 = APPLICATION_CONTEXT('core data for automotive mechanical design processes');
#3 = SHAPE_DEFINITION_REPRESENTATION(#4,#10);
#4 = PRODUCT_DEFINITION_SHAPE('','',#5);
#5 = PRODUCT_DEFINITION('design','',#6,#9);
#6 = PRODUCT_DEFINITION_FORMATION('','',#7);
#7 = PRODUCT('LiPo_cell','LiPo_cell','',(#8));
#8 = PRODUCT_CONTEXT('',#2,'mechanical');
#9 = PRODUCT_DEFINITION_CONTEXT('part definition',#2,'design');
#10 = ADVANCED_BREP_SHAPE_REPRESENTATION('',(%s,%s),#20);
#11 = PRODUCT_RELATED_PRODUCT_CATEGORY('part',$,(#7));
#20 = ( GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#21)) GLOBAL_UNIT_ASSIGNED_CONTEXT((#22,#23,#24)) REPRESENTATION_CONTEXT('Context #1','3D Context with UNIT and UNCERTAINTY') );
#21 = UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-07),#22,'distance_accuracy_value','confusion accuracy');
#22 = ( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) );
#23 = ( NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.) );
#24 = ( NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT() );
%s
ENDSEC;
END-ISO-10303-21;
""" % (origin, brep, body)
    open(OUT, 'w').write(txt)
    print(os.path.relpath(OUT), len(ents), 'entities')


if __name__ == '__main__':
    main()
