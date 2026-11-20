#!/usr/bin/env bash
# Route the freshly generated FujiNet-Pocket-Rev0.kicad_pcb (tools/gen_pcb.py) and finish it:
# Freerouting, the grid A* finisher for what it leaves, clean-up, GND stitching, 3D models,
# silkscreen, and the DRC gate (FujiNet-7800-Rev0's flow without its RP2354B pre-route).
# Freerouting 2.4.1 needs Java 25: JAVA names the binary when the default java is older.
# PASSES sets Freerouting's pass budget.
set -euo pipefail
cd "$(dirname "$0")/.."
PCB=FujiNet-Pocket-Rev0.kicad_pcb
PY=${PCBNEW_PYTHON:-/usr/bin/python3}     # the Python that has KiCad's pcbnew module
$PY tools/route.py --passes "${PASSES:-20}"
$PY tools/drc_fix.py                      # drop router copper that breaks DRC; the finisher redoes it
$PY tools/finish_route.py || true
$PY tools/drc_fix.py
$PY tools/finish_route.py || echo 'finish_route: links left open -- the DRC gate below will fail'
$PY tools/tidy_tracks.py
$PY tools/stitch_gnd.py                   # GND stitching grid + edge guard row, DRC-filtered
$PY tools/check_vias.py
$PY tools/set_models.py
$PY tools/fix_silk.py                     # refs off pads/other silk (nearest clear spot, else hidden)
$PY tools/fill_zones.py
kicad-cli pcb drc --schematic-parity --severity-error --exit-code-violations $PCB -o /dev/null
