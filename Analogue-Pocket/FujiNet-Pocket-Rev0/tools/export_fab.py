#!/usr/bin/env python3
"""Fabrication, documentation and shell outputs for FujiNet Pocket Rev0 (DRAFT):

  exports/FujiNet-Pocket-Rev0-gerbers.zip   gerbers (4 copper layers) + Excellon drill (PTH / NPTH)
  exports/FujiNet-Pocket-Rev0-pos.csv       KiCad's own placement file, front only (no part on the back)
  exports/FujiNet-Pocket-Rev0.step          the board with every model and the cell stand-in: the
                                            starting point for the shell (case/board-anchors.*)
  docs/board-top.png, docs/board-bottom.png 3D renders
  docs/layout-front.svg, docs/layout-back.svg

Not done here (FujiNet-7800-Rev0's export.py does them for that board): JLCPCB's CPL rotation
corrections and the per-fab BOMs.  Check the placement preview at the fab before paying.

Usage: python3 tools/export_fab.py      (after the board is routed)
"""
import os, subprocess, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tmpdir import tmp
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
PCB = os.path.join(PRJ, D.PROJECT + '.kicad_pcb')
EXP = os.path.join(PRJ, 'exports')
DOCS = os.path.join(PRJ, 'docs')


def run(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit('failed: ' + ' '.join(a))
    return r.stdout


def gerbers():
    d = tmp('gerbers')
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    layers = 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts'
    run('kicad-cli', 'pcb', 'export', 'gerbers', '--check-zones', '--layers', layers, '--subtract-soldermask',
        '-o', d + '/', PCB)
    run('kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th',
        '--generate-map', '--map-format', 'gerberx2', '-o', d + '/', PCB)
    out = os.path.join(EXP, D.PROJECT + '-gerbers.zip')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(d)):
            z.write(os.path.join(d, f), f)
    return out


def main():
    os.makedirs(EXP, exist_ok=True)
    os.makedirs(DOCS, exist_ok=True)
    print(os.path.relpath(gerbers(), PRJ))
    pos = os.path.join(EXP, D.PROJECT + '-pos.csv')
    run('kicad-cli', 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'front',
        '--exclude-dnp', '-o', pos, PCB)
    step = os.path.join(EXP, D.PROJECT + '.step')
    run('kicad-cli', 'pcb', 'export', 'step', '--subst-models', '--no-dnp', '--force', '-o', step, PCB)
    run('kicad-cli', 'pcb', 'export', 'svg', '--layers', 'F.Cu,F.SilkS,F.Mask,Edge.Cuts', '--mode-single',
        '--page-size-mode', '2', '--exclude-drawing-sheet', '-o', os.path.join(DOCS, 'layout-front.svg'), PCB)
    run('kicad-cli', 'pcb', 'export', 'svg', '--layers', 'B.Cu,B.SilkS,B.Mask,Edge.Cuts', '--mode-single', '--mirror',
        '--page-size-mode', '2', '--exclude-drawing-sheet', '-o', os.path.join(DOCS, 'layout-back.svg'), PCB)
    for side, name in (('top', 'board-top.png'), ('bottom', 'board-bottom.png')):
        run('kicad-cli', 'pcb', 'render', '--side', side, '--width', '1400', '--height', '1100',
            '--quality', 'high', '--zoom', '1.0', '-o', os.path.join(DOCS, name), PCB)
    for f in (pos, step):
        print(os.path.relpath(f, PRJ))
    print('docs: board-top.png, board-bottom.png, layout-front.svg, layout-back.svg')


if __name__ == '__main__':
    main()
